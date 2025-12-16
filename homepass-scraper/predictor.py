import json
import os
import re
import joblib
import pandas as pd
import numpy as np
import pymysql
from datetime import datetime

# 1군 건설사 리스트 (모델 학습 때와 동일해야 함)
TOP_BRANDS = [
    "삼성물산",
    "현대건설",
    "DL이앤씨",
    "포스코이앤씨",
    "GS건설",
    "대우건설",
    "현대엔지니어링",
    "롯데건설",
    "SK에코플랜트",
    "HDC현대산업개발",
]

# DB 설정
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "db": os.getenv("DB_NAME"),
    "port": int(os.getenv("DB_PORT")),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


def load_model_assets():
    """모델과 전처리기 로드"""
    try:
        model = joblib.load("catboost_model_except_top_brand.pkl")
        print("✅ 모델 및 전처리기 로드 완료")
        return model
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        exit()


def preprocess_and_predict_group(row, model):

    # 1. 공통 정보 파싱
    announcement_id = row["announcement_id"]
    source_org = row["source_organization"]
    address = row["address_detail"]
    total_households = row["total_households"] if row["total_households"] else 0
    post_date = row["post_date"]
    price_json_str = row["price"]

    year = post_date.year if post_date else datetime.now().year
    month = post_date.month if post_date else datetime.now().month
    region_str = str(address).split()[0] if address else "Unknown"

    if not price_json_str:
        return None

    try:
        price_list = json.loads(price_json_str)
    except:
        return None

    if not price_list:
        return None

    # -------------------------------------------------------
    # [단계 1] 데이터 파싱 및 그룹핑 키 생성
    # -------------------------------------------------------
    parsed_items = []
    for idx, item in enumerate(price_list):
        try:
            # (1) 면적 추출
            raw_type = str(item.get("타입") or "")
            match = re.search(r"(\d+(\.\d+)?)", raw_type)
            area = float(match.group(1)) if match else 0
            if area <= 0:
                continue

            # (2) 가격 환산 (매매가 기준)
            deposit_val = float(item.get("보증금(만원)") or 0)
            rent_val = float(item.get("임대료(만원)") or 0)

            # 전세 환산 = 보증금 + (월세 * 200) -> 매매가 환산 (/ 0.6)
            if row["housing_type"] == "청년안심주택":
                price_amt = (deposit_val + rent_val * 200) / 0.6
            else:
                price_amt = deposit_val
            pyung_price = price_amt / (area / 3.3058)

            # (3) 공급 유형 확인
            supply_type = "일반" if "일반" in item.get("공급유형1", "") else "특별"

            # (4) 그룹핑 키 생성 (타입명 + 공급유형)
            # 예: "40.61㎡ (40B)_특별"
            group_key = f"{raw_type}_{supply_type}"

            parsed_items.append(
                {
                    "original_idx": idx,  # 원본 리스트에서의 인덱스 (나중에 값 넣을 때 필요)
                    "group_key": group_key,  # 그룹 식별자
                    "LTTOT_TOP_AMOUNT": price_amt,
                    "PRICE_PER_PYUNG": pyung_price,
                    "deposit_val": deposit_val,  # 대표 선출용 (보증금 높은 순)
                    # 모델 입력용 데이터
                    "TOTAL_UNIT_CNT": total_households,
                    "AREA_SIZE": area,
                    "CNSTRCT_ENTRPS_NM": source_org,
                    "REGION": region_str,
                    "YEAR": year,
                    "MONTH": month,
                }
            )

        except Exception:
            continue

    if not parsed_items:
        return None

    # -------------------------------------------------------
    # [단계 2] 그룹별 대표 선수 선발 (보증금 가장 높은 항목)
    # -------------------------------------------------------
    df = pd.DataFrame(parsed_items)

    representative_indices = df.groupby("group_key")["deposit_val"].idxmax()
    representative_df = df.loc[representative_indices].copy()

    # -------------------------------------------------------
    # [단계 3] 대표 항목 예측 수행
    # -------------------------------------------------------
    # 모델에 필요한 컬럼만 선택
    feature_cols = [
        "LTTOT_TOP_AMOUNT",
        "PRICE_PER_PYUNG",
        "TOTAL_UNIT_CNT",
        "AREA_SIZE",
        "CNSTRCT_ENTRPS_NM",
        "REGION",
        "YEAR",
        "MONTH",
    ]

    # 예측 (predict_proba)
    probs = model.predict_proba(representative_df[feature_cols])

    preds = []
    for p in probs:
        p2 = p[2]  # 인기 등급 확률
        p1 = p[1]  # 보통 등급 확률
        if p2 > 0.2:
            preds.append(2)
        elif p1 > 0.4:
            preds.append(1)
        else:
            preds.append(0)

    representative_df["predicted_tier"] = preds

    # -------------------------------------------------------
    # [단계 4] 결과를 원본 리스트에 전파 (Broadcast)
    # -------------------------------------------------------
    tier_map = representative_df.set_index("group_key")["predicted_tier"].to_dict()

    # 원본 price_list를 순회하며 결과 주입
    for item_data in parsed_items:
        g_key = item_data["group_key"]
        orig_idx = item_data["original_idx"]

        if g_key in tier_map:
            tier = int(tier_map[g_key])
            price_list[orig_idx]["예측경쟁률"] = tier

    return price_list


if __name__ == "__main__":
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM Announcements WHERE housing_type='청년안심주택' or source_organization='청약홈'"
    )
    rows = cursor.fetchall()

    if not rows:
        print("업데이트할 데이터가 없습니다.")
        exit()

    model = load_model_assets()

    update_count = 0
    print("--- 예측 및 업데이트 시작 ---")
    for row in rows:
        try:
            updated_price_list = preprocess_and_predict_group(row, model)

            if updated_price_list:
                # 2. DB 업데이트
                new_json_str = json.dumps(updated_price_list, ensure_ascii=False)
                update_sql = (
                    "UPDATE Announcements SET price = %s WHERE announcement_id = %s"
                )
                cursor.execute(update_sql, (new_json_str, row["announcement_id"]))
                update_count += 1

                if update_count % 100 == 0:
                    conn.commit()
                    print(f"... {update_count}건 처리됨")

        except Exception as e:
            print(f"Error ID {row['announcement_id']}: {e}")
            continue

    conn.commit()
    conn.close()
    print(f"✅ 총 {update_count}건의 공고 업데이트 완료")
