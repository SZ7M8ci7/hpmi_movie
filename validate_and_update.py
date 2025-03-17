import pandas as pd
import sys
import shutil

def load_csv(file_path):
    df = pd.read_csv(file_path, header=None)
    return df

def validate_monotonic_increase(old_df, new_df):
    # 最初の2列（地域名、映画館名）と最後の列（URL）は検証対象外
    numeric_old = old_df.iloc[:, 3:-1]
    numeric_new = new_df.iloc[:, 3:-1]
    
    if not (numeric_new >= numeric_old).all().all():
        raise ValueError("数値が単調増加していません。")

def main():
    old_csv = "battle_results.csv"
    temp_csv = "battle_results_temp.csv"
    
    old_df = load_csv(old_csv)
    new_df = load_csv(temp_csv)
    
    try:
        validate_monotonic_increase(old_df, new_df)
        shutil.move(temp_csv, old_csv)
        print("ファイルが正常に更新されました。")
    except ValueError as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
