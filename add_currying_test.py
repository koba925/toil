import os

# 検索する対象の文字列（インデントに注意して完全一致させます）
target_pattern = """        assert toil.walk(r\"\"\"
            a := 2;
            f := func do a end;
            g := func do a := 3; f() end;
            g()
        \"\"\") == 2"""

# 挿入するテストコード
insert_text = """

        assert toil.walk(r\"\"\"
            func a do func b do a + b end end (2)(3)
        \"\"\") == 5"""

def main():
    # bookフォルダを起点にする
    book_dir = "book"
    if not os.path.exists(book_dir):
        print(f"Error: '{book_dir}' ディレクトリが見つかりません。")
        return

    # book以下のディレクトリを走査
    for dirname in sorted(os.listdir(book_dir)):
        dir_path = os.path.join(book_dir, dirname)

        # ディレクトリかつ、名前が "0216" 以降で始まるものだけを対象とする
        if os.path.isdir(dir_path) and dirname >= "0216":
            test_file = os.path.join(dir_path, "test_twi.py")

            if os.path.exists(test_file):
                with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # すでに追加済みでなければ置換を実行
                if target_pattern in content:
                    if insert_text not in content:
                        new_content = content.replace(target_pattern, target_pattern + insert_text)
                        with open(test_file, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"✅ Updated: {test_file}")
                    else:
                        print(f"⏭️ Already updated: {test_file}")
                else:
                    print(f"⚠️ Pattern not found: {test_file}")

if __name__ == "__main__":
    main()