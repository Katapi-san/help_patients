import streamlit as st
import requests

def fetch_studies_v2(cond_value, overall_status_value, location_value):
    """
    ClinicalTrials.gov v2 API (Beta) からデータを取得する関数。
    :param cond_value: query.cond に相当。例: "lung cancer" など
    :param overall_status_value: filter.overallStatus に相当。例: "RECRUITING" など
    :param location_value: query.locn に相当。例: "Japan" など
    :return: API レスポンス(JSON)を Python の辞書 として返す
    """

    base_url = "https://clinicaltrials.gov/api/v2/studies"

    params = {
        "query.cond": cond_value,                  # 病名や状態など
        "filter.overallStatus": overall_status_value,  # RECRUITING など
        "query.locn": location_value               # 実施国や場所
        # 必要に応じて "pageSize" や "page" パラメータを追加する
    }

    response = requests.get(base_url, params=params)

    # 4xx/5xx エラー時は例外を投げる
    response.raise_for_status()

    return response.json()


def main():
    st.title("ClinicalTrials.gov v2 検索ツール（ベータ版）")

    # 入力フォーム
    cond_value = st.text_input("Condition (query.cond)", "lung cancer")
    overall_status_value = st.text_input("Overall Status (filter.overallStatus)", "RECRUITING")
    location_value = st.text_input("Location (query.locn)", "Japan")

    # 検索ボタン押下時に API 呼び出し
    if st.button("Search"):
        try:
            data = fetch_studies_v2(cond_value, overall_status_value, location_value)
            st.write("検索パラメータ:", {
                "query.cond": cond_value,
                "filter.overallStatus": overall_status_value,
                "query.locn": location_value
            })

            # 取得データを表示
            st.write("取得データ:")
            st.json(data)  # Streamlit の json 表示

        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e}")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
