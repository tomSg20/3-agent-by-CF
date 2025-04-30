import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from dotenv import load_dotenv
import os
import json
from pathlib import Path


# Load environment variables for API credentials (optional, for security)
load_dotenv()

# Cloudflare API credentials (replace with your values or use environment variables)
#CLOUDFLARE_AUTH_TOKEN = os.getenv("CLOUDFLARE_AUTH_TOKEN", "your-auth-token-here")
#CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "your-account-id-here")
#CLOUDFLARE_MODEL = "@cf/meta/llama-3.1-8b-instruct"  # Model for Cloudflare AI
CLOUDFLARE_AUTH_TOKEN = os.getenv("CLOUDFLARE_AUTH_TOKEN", "")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")

CLOUDFLARE_MODEL = "@cf/google/gemma-3-12b-it"  # Model for Cloudflare AI


def remove_first_and_last_lines(text):
    """
    Removes the first and last lines from a multi-line text string.

    Args:
    text: A string containing multiple lines of text.

    Returns:
    A string containing the text with the first and last lines removed.
    Returns an empty string if the input text has less than 3 lines.
    """
    lines = text.splitlines()
    if not text.startswith('```'):return text
    if len(lines) < 3:
        return text  # Or raise an exception if you prefer, e.g., ValueError("Text must have at least 3 lines")
    else:
        return "\n".join(lines[1:-1])



def cloudflare_chat_completion(auth_token, account_id, model, messages):
    """
    Send a chat completion request to the Cloudflare AI API.

    Args:
        auth_token (str): Authorization token for the API.
        account_id (str): Cloudflare account ID.
        model (str): The model to use, e.g., "@cf/meta/llama-3.1-8b-instruct".
        messages (list of dict): Chat messages with role and content, e.g.,
                                 [{"role": "user", "content": "Your question"}].

    Returns:
        dict: The JSON response from the Cloudflare API.
    """
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

class CloudflareChatApp:
    def __init__(self, root):
        """Initialize the Tkinter application with UI components and two tables."""
        self.root = root
        self.root.title("Cloudflare AI Chat Interface with Two Tables")
        self.root.geometry("1200x800")  # Increased width to accommodate two tables

        # Configure the main grid layout for three columns
        self.root.grid_columnconfigure(0, weight=1)  # Column for text areas
        self.root.grid_columnconfigure(1, weight=0)  # Column for buttons
        self.root.grid_columnconfigure(2, weight=1)  # Column for second table
        self.root.grid_rowconfigure((0, 1, 2, 3), weight=1)  # Rows for text areas
        self.root.grid_rowconfigure(4, weight=2)  # Row for tables
        self.root.grid_rowconfigure(5, weight=0)  # Extra row if needed

        # Initial sample data for the first table
        self.table_data_1 = [
            ["1", "银行存款", "收回维力贸易公司前欠购货款", "52100", ""],
            ["1", "应收账款-维力贸易公司", "收回前欠购货款", "", "52100"],
            ["", "", "合计", "52100", "52100"]
        ]

        # Initial sample data for the second table (can be different)
        self.table_data_2 = [
            ["2", "库存商品", "采购商品入库", "10000", ""],
            ["2", "应付账款", "采购商品未付款", "", "10000"],
            ["", "", "合计", "10000", "10000"]
        ]

        # Define system prompts for different AI agents
        self.system_prompts = {
            "agent_1": 
'''
你是一名会计师，根据最新中国会计准则和我的输入制作会计凭证。会计凭证的格式为json和表格，包括（编号，科目，摘要，借方金额，贷方金额）。增值税率为13%。
# 凭证制作要求
1. 在输出时候请确认借贷平衡。
2. 在金额含税的情况下根据增值税率计算进项或者销项的金额，方便在凭证中使用。
3. 当出现熟悉公式时计算公式，例如：输入 1000*10 ，返回 10000。
# 科目要求
1. 一级科目选择要遵守最新的中国的企业会计准则。 参考（https://www.zkemu.com/acc4/u/kjkm/）


Json示例：
{
"明细": [
{
"编号": "1",
"科目": "银行存款",
"摘要": "收回维力贸易公司前欠购货款",
"借方金额": "52100",
"贷方金额": null
},
{
"编号": "1",
"科目": "应收账款-维力贸易公司",
"摘要": "收回前欠购货款",
"借方金额": null,
"贷方金额": "52100"
}
],
"合计": {
"借方合计": 52100,
"贷方合计": 52100
}
}
。
对Json对象进行计算。“借方合计”和“贷方合计”为“明细"中的合计金额。
如果“借方合计”和“贷方合计”不一致则代表借贷不平衡（“借方合计”和“贷方合计”是汇总“明细”里面的金额，请执行校验步骤避免错误）。

表格示例：

| 编号 | 科目               | 摘要                     | 借方金额 | 贷方金额 |
|------|--------------------|--------------------------|----------|----------|
| 1    | 银行存款           | 收回维力贸易公司前欠购货款 | 52100    |          |
| 1    | 应收账款-维力贸易公司 | 收回前欠购货款             |          | 52100    |
| |  |  合计 | 52100    | 52100    |

。

''',

            "agent_2":
'''
please only return the json object in the input
''',

            "agent_3": "You are a legal consultant for financial agreements. Provide guidance on contracts and obligations."
        }

        # Create and configure UI elements (Text Areas, Buttons, and Two Tables)
        self.setup_ui()

        self.total_label = tk.Label(
            root,
            text="",
            font=("Arial", 12, "bold"),
            anchor="w"
        )


        # Initialize table with data from all JSON files
        self.load_all_json_files()


    def setup_ui(self):
        """Set up the UI components like text areas, buttons, and two tables with proper layout."""
        # Labels and Text Areas for Input/Output
        self.labels = []
        self.text_areas = []
        for i in range(4):
            label = ttk.Label(self.root, text=f"Text Area {i+1}")
            label.grid(row=i, column=0, padx=5, pady=5, sticky="nw")
            self.labels.append(label)

            text_area = tk.Text(self.root, height=5, wrap=tk.WORD)
            text_area.grid(row=i, column=0, padx=5, pady=5, sticky="nsew")
            self.text_areas.append(text_area)

        # Buttons to trigger Cloudflare AI API calls, clear action, and table updates
        self.buttons = []
        button_configs = [
            ("Ask Financial Advisor (Agent 1)", self.ask_agent_1),
            ("Ask Data Analyst (Agent 2)", self.ask_agent_2),
            ("Ask Legal Consultant (Agent 3)", self.ask_agent_3),
            ("Clear All", self.clear_all),
            ("Update Table 1 (Test)", self.update_table_1_test),
            ("Update Table 2 (Test)", self.update_table_2_test)  # Added button for second table
        ]
        for i, (label, command) in enumerate(button_configs):
            btn = ttk.Button(self.root, text=label, command=command)
            btn.grid(row=i, column=1, padx=5, pady=5, sticky="ew")  # Place buttons in column 1
            self.buttons.append(btn)

        # Set up the first table in column 0, row 4
        self.setup_table_1()

        # Set up the second table in column 2, row 4
        self.setup_table_2()

    def setup_table_1(self):
        """Set up the first table using ttk.Treeview in column 0, row 4."""
        headers = ["编号", "科目", "摘要", "借方金额", "贷方金额"]
        tree_frame = ttk.Frame(self.root)
        tree_frame.grid(row=4, column=0, padx=5, pady=5, sticky="nsew")  # Place in column 0
        self.tree_1 = ttk.Treeview(tree_frame, columns=headers, show="headings", height=8)
        for header in headers:
            self.tree_1.heading(header, text=header)
            self.tree_1.column(header, width=120, anchor=tk.CENTER)
        for row in self.table_data_1:
            self.tree_1.insert("", "end", values=row)
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_1.yview)
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_1.xview)
        self.tree_1.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)
        tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x.pack(side="bottom", fill="x")
        self.tree_1.pack(side="left", fill="both", expand=True)

    def setup_table_2(self):
        """Set up the second table using ttk.Treeview in column 2, row 4."""
        headers = ["编号", "科目", "摘要", "借方金额", "贷方金额"]
        tree_frame = ttk.Frame(self.root)
        tree_frame.grid(row=4, column=2, padx=5, pady=5, sticky="nsew")  # Place in column 2
        self.tree_2 = ttk.Treeview(tree_frame, columns=headers, show="headings", height=8)
        for header in headers:
            self.tree_2.heading(header, text=header)
            self.tree_2.column(header, width=120, anchor=tk.CENTER)
        for row in self.table_data_2:
            self.tree_2.insert("", "end", values=row)
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_2.yview)
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_2.xview)
        self.tree_2.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)
        tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x.pack(side="bottom", fill="x")
        self.tree_2.pack(side="left", fill="both", expand=True)

    def update_table(self, json_data, table_tree):
        """
        Update the specified table with data from a JSON string or dictionary.

        Args:
            json_data (str or dict): JSON string or parsed dictionary containing table data.
            table_tree (ttk.Treeview): The Treeview widget to update (either tree_1 or tree_2).
        """
        if isinstance(json_data, str):
            try:
                data = json.loads(json_data)
            except json.JSONDecodeError as e:
                messagebox.showerror("JSON Error", f"Invalid JSON data: {str(e)}")
                return
        else:
            data = json_data

        # Clear existing table data
        for item in table_tree.get_children():
            table_tree.delete(item)

        # Insert detailed entries
        details = data.get("明细", [])
        for entry in details:
            row = [
                entry.get("编号", ""),
                entry.get("科目", ""),
                entry.get("摘要", ""),
                entry.get("借方金额", "") if entry.get("借方金额") is not None else "",
                entry.get("贷方金额", "") if entry.get("贷方金额") is not None else ""
            ]
            table_tree.insert("", "end", values=row)

        # Insert summary row
        summary = data.get("合计", {})
        if summary:
            summary_row = [
                "", "", "合计",
                summary.get("借方合计", "") if summary.get("借方合计") is not None else "",
                summary.get("贷方合计", "") if summary.get("贷方合计") is not None else ""
            ]
            table_tree.insert("", "end", values=summary_row)

    def update_table_1_test(self):
        """Test method to update the first table with sample JSON data."""
        sample_json = '''
        {
          "明细": [
            {
              "编号": "1",
              "科目": "库存现金",
              "摘要": "从银行提取备用金",
              "借方金额": "3000",
              "贷方金额": null
            },
            {
              "编号": "1",
              "科目": "银行存款",
              "摘要": "提取备用金",
              "借方金额": null,
              "贷方金额": "3000"
            }
          ],
          "合计": {
            "借方合计": 3000,
            "贷方合计": 3000
          }
        }
        '''
        source_text = self.text_areas[2].get(1.0, tk.END).strip()
        temp = remove_first_and_last_lines(source_text)
        sample_json = temp
        self.text_areas[2].delete(1.0, tk.END)
        self.text_areas[2].insert(tk.END, temp)
        self.update_table(sample_json, self.tree_1)

    def update_table_2_test(self):
        """Test method to update the second table with sample JSON data (different data for demo)."""
        sample_json = '''
        {
          "明细": [
            {
              "编号": "2",
              "科目": "库存商品",
              "摘要": "采购商品入库",
              "借方金额": "5000",
              "贷方金额": null
            },
            {
              "编号": "2",
              "科目": "应付账款",
              "摘要": "采购商品未付款",
              "借方金额": null,
              "贷方金额": "5000"
            }
          ],
          "合计": {
            "借方合计": 5000,
            "贷方合计": 5000
          }
        }
        '''
        self.update_table(sample_json, self.tree_2)

    def ask_agent_1(self):
        """Handle button click for 'Ask Financial Advisor (Agent 1)' (Text Area 1 to Text Area 2)."""
        self.get_cloudflare_response(0, 1, 0, "agent_1")

    def ask_agent_2(self):
        """Handle button click for 'Ask Data Analyst (Agent 2)' (Text Area 2 to Text Area 3)."""
        self.get_cloudflare_response(1, 2, 1, "agent_2")

    def ask_agent_3(self):
        """Handle button click for 'Ask Legal Consultant (Agent 3)' (Text Area 3 to Text Area 4)."""
        self.get_cloudflare_response(2, 3, 2, "agent_3")

    def clear_all(self):
        """Handle button click for 'Clear All' to clear all text areas."""
        for text_area in self.text_areas:
            text_area.delete(1.0, tk.END)

    def get_cloudflare_response(self, source_area_idx, target_area_idx, button_idx, agent_key):
        """
        Fetch response from Cloudflare AI API based on input from source text area
        and display it in target text area, using a specific agent configuration.
        """
        source_text = self.text_areas[source_area_idx].get(1.0, tk.END).strip()
        if not source_text:
            messagebox.showwarning("Input Error", "Please enter a question!")
            return
        self.buttons[button_idx].config(state="disabled")
        self.text_areas[target_area_idx].delete(1.0, tk.END)
        self.text_areas[target_area_idx].insert(tk.END, "Fetching response...\n")
        thread = threading.Thread(target=self.fetch_cloudflare_response,
                                 args=(source_text, target_area_idx, button_idx, agent_key))
        thread.daemon = True
        thread.start()

    def fetch_cloudflare_response(self, question, target_area_idx, button_idx, agent_key):
        """
        Fetch response from Cloudflare AI API in a separate thread and update UI.
        """
        try:
            messages = [
                {"role": "system", "content": self.system_prompts.get(agent_key, "You are a helpful assistant.")},
                {"role": "user", "content": question}
            ]
            response = cloudflare_chat_completion(
                CLOUDFLARE_AUTH_TOKEN,
                CLOUDFLARE_ACCOUNT_ID,
                CLOUDFLARE_MODEL,
                messages
            )
            if "error" in response:
                answer = f"Error: {response['error']}"
            else:
                answer = response.get("choices", [{}])[0].get("message", {}).get("content", "No content received")
            self.root.after(0, self.update_text_area, target_area_idx, answer, button_idx)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, self.update_text_area, target_area_idx, error_msg, button_idx)

    def update_text_area(self, target_area_idx, text, button_idx):
        """
        Update the target text area with the response and re-enable the button.
        """
        self.text_areas[target_area_idx].delete(1.0, tk.END)
        self.text_areas[target_area_idx].insert(tk.END, text)
        self.buttons[button_idx].config(state="normal")
    ## --- Table Functions ---
    def calculate_total(self, table_rows):
        total_debit = sum(int(row.get("借方金额")) if row.get("借方金额") else 0 for row in table_rows)
        total_credit = sum(int(row.get("贷方金额")) if row.get("贷方金额") else 0 for row in table_rows)
        return total_debit, total_credit

    def init_json(self, table_rows):
        """Initialize or update the table with the provided rows."""
        print(table_rows)
        if not hasattr(self, 'tree_2'):
            return  # Safeguard in case tree is not initialized
        for i in self.tree_2.get_children():
            self.tree_2.delete(i)
        for row in table_rows:
            values = [
                row.get("编号", ""),
                row.get("科目", ""),
                row.get("摘要", ""),
                row.get("借方金额") if row.get("借方金额") else "",
                row.get("贷方金额") if row.get("贷方金额") else ""
            ]
            self.tree_2.insert("", "end", values=values)
        total_debit, total_credit = self.calculate_total(table_rows)
        total_row = ["合计", "", "", total_debit, total_credit]
        self.tree_2.insert("", "end", values=total_row)
        self.total_label.config(text=f"借方合计: {total_debit}    贷方合计: {total_credit}")
        return total_debit, total_credit

    def load_all_json_files(self):
        print("R")
        """Load all JSON files from the current directory and display their data in the table."""
        if not hasattr(self, 'tree_2'):
            return  # Safeguard in case tree is not initialized
        all_data = []
        current_dir = Path.cwd()
        json_files = current_dir.glob("*.json")
        print(json_files)

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    if "明细" in file_data:
                        all_data.extend(file_data["明细"])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {json_file.name}: {str(e)}")

        if all_data:
            print(all_data)
            self.init_json(all_data)
        else:
            messagebox.showinfo("Info", "No valid JSON data found to display in the table.")
            self.init_json(data["明细"])  # Fallback to sample data if no JSON files are found


def main():
    """Main function to run the Tkinter application."""
    root = tk.Tk()
    app = CloudflareChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
