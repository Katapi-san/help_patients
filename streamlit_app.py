import streamlit as st
import requests
import pandas as pd

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
        "filter.overallStatus": overall_status_value,  # RECRUITING など (ベータ仕様)
        "query.locn": location_value               # 実施場所 (ベータ仕様)
        # 必要に応じて "pageSize" や "page" パラメータを追加する
    }

    response = requests.get(base_url, params=params)

    # 4xx/5xx エラー時は例外を投げる
    response.raise_for_status()

    return response.json()


def parse_studies_to_table(json_data):
    """
    レスポンスの JSON から特定の項目を抽出し、pandas DataFrame を返す。
    以下のキーを想定:
      - nctId
      - title -> Study Title
      - studyPageUrl -> Study URL
      - status -> Study Status
      - briefSummary -> Brief Summary
      - conditions -> Conditions
      - interventions -> Interventions
      - sponsor -> Sponsor (文字列を想定)
      - phase -> Phases (単一または複数を想定)
      - startDate -> Start Date
      - primaryCompletionDate -> Primary Completion Date
      - completionDate -> Completion Date
      - lastUpdatePostDate -> Last Update Posted
    """
    # v2 のレスポンス構造例:
    # {
    #   "data": {
    #       "studies": [
    #           {
    #               "nctId": "...",
    #               "title": "...",
    #               "studyPageUrl": "...",
    #               "status": "...",
    #               "briefSummary": "...",
    #               "conditions": [...],
    #               "interventions": [...],
    #               "sponsor": { ... }, or sponsor: "some string"
    #               "phase": "Phase 2" or ["Phase 1", "Phase 2"]
    #               "startDate": "2023-01-01",
    #               "primaryCompletionDate": "...",
    #               "completionDate": "...",
    #               "lastUpdatePostDate": "2023-09-01"
    #           },
    #           ...
    #       ]
    #   }
    # }

    # "data" -> "studies" があるかチェック
    if not isinstance(json_data, dict) or "data" not in json_data:
        return pd.DataFrame()  # 空の DataFrame

    studies_data = json_data["data"].get("studies", [])
    if not isinstance(studies_data, list):
        return pd.DataFrame()

    # 1 研究につき 1 行を作るイメージ
    table_rows = []

    for study in studies_data:
        # それぞれのキーを取り出し(なければデフォルト)
        nct_id = study.get("nctId", "")
        title = study.get("title", "")
        study_url = study.get("studyPageUrl", "")
        status = study.get("status", "")
        brief_summary = study.get("briefSummary", "")

        # conditions, interventions は配列の場合があるので、"," で連結
        conditions = study.get("conditions", [])
        if isinstance(conditions, list):
            conditions = ", ".join(conditions)

        interventions = study.get("interventions", [])
        if isinstance(interventions, list):
            interventions = ", ".join(interventions)

        # sponsor は文字列か、辞書かで取得の方法が変わるかもしれない
        # ここではとりあえず文字列として統一 (辞書の場合は"name"を取得するなど要確認)
        sponsor = study.get("sponsor", "")
        if isinstance(sponsor, dict):
            # 例: sponsor の中に name があると仮定
            sponsor = sponsor.get("name", "") or sponsor.get("agency", "")

        # phase は単一文字列のこともあれば、配列のこともあるかもしれない
        phase = study.get("phase", "")
        if isinstance(phase, list):
            phase = ", ".join(phase)

        start_date = study.get("startDate", "")
        primary_completion_date = study.get("primaryCompletionDate", "")
        completion_date = study.get("completionDate", "")
        last_update_posted = study.get("lastUpdatePostDate", "")

        row = {
            "nctId": nct_id,
            "Study Title": title,
            "Study URL": study_url,
            "Study Status": status,
            "Brief Summary": brief_summary,
            "Conditions": conditions,
            "Interventions": interventions,
            "Sponsor": sponsor,
            "Phases": phase,
            "Start Date": start_date,
            "Primary Completion Date": primary_completion_date,
            "Completion Date": completion_date,
            "Last Update Posted": last_update_posted
        }
        table_rows.append(row)

    df = pd.DataFrame(table_rows)
    return df


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

            # JSON全体をデバッグ表示したい場合:
            # st.json(data)

            # 取得データからテーブル生成
            df = parse_studies_to_table(data)
            if df.empty:
                st.write("検索結果がないか、抽出できるデータがありませんでした。")
            else:
                st.write("検索結果テーブル:")
                st.dataframe(df)  # 表形式で表示

        except requests.exceptions.HTTPError as e:
            st.error(f"HTTP Error: {e}")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")


if __name__ == "__main__":
    main()
