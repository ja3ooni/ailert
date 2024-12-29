import os
import subprocess

default_cred = ""

class KaggleScanner:
    def __init__(self, base_url, top_n=5, kaggle_cred_path=default_cred):
        self.base_url = base_url
        self.top_n = top_n
        self.kaggle_cred_path = kaggle_cred_path
        self.response = []

    def __get_top_n_kaggle_competitions(self, top_n):
        try:
            os.environ["KAGGLE_CONFIG_DIR"] = os.path.expanduser(self.kaggle_cred_path)
            result = subprocess.run(
                ["kaggle", "competitions", "list", "--sort-by", "recentlyCreated"],
                stdout=subprocess.PIPE,
                text=True
            )
            if result.returncode != 0:
                print("Error fetching Kaggle competitions:", result.stderr)
                return

            lines = result.stdout.strip().split("\n")
            data_rows = [line for line in lines if "https://www.kaggle.com" in line]
            response = []

            for row in data_rows[:top_n]:
                columns = row.split()
                if len(columns) > 0:
                    competition_link = columns[0]
                    deadline = columns[1]
                    reward = columns[3]

                    competition_name = competition_link.split("/")[-1]

                    response.append({
                        "Name": competition_name,
                        "Link": competition_link,
                        "Deadline": deadline,
                        "Reward": reward
                    })
            return response
        except Exception as e:
            print(f"Error: {e}")

    def get_new_competitions_launch(self):
        kaggle_response = self.__get_top_n_kaggle_competitions(self.top_n, self.kaggle_cred_path)

        self.response.append(kaggle_response)
        return self.response
