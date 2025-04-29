import tkinter as tk
from tkinter import ttk, messagebox
import requests
import threading
from dotenv import load_dotenv
import os

# Load environment variables for API credentials (optional, for security)
load_dotenv()

# Cloudflare API credentials (replace with your values or use environment variables)
CLOUDFLARE_AUTH_TOKEN = os.getenv("CLOUDFLARE_AUTH_TOKEN", "your-auth-token-here")
CLOUDFLARE_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "your-account-id-here")
CLOUDFLARE_MODEL = "@cf/meta/llama-3.1-8b-instruct"  # Model for Cloudflare AI

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
    # Define the payload with the model and message(s)
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096
    }

    try:
        # Make a POST request to the API
        response = requests.post(url, headers=headers, json=data)

        # Raise an error if the request was unsuccessful
        response.raise_for_status()

        # Return the response JSON data
        return response.json()
    except requests.exceptions.RequestException as e:
        # Handle and return any errors encountered during the request
        return {"error": str(e)}

class CloudflareChatApp:
    def __init__(self, root):
        """Initialize the Tkinter application with UI components and a table."""
        self.root = root
        self.root.title("Cloudflare AI Chat Interface with Table")
        self.root.geometry("800x800")  # Adjusted window size to accommodate table

        # Configure the main grid layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure((0, 1, 2, 3), weight=1)
        self.root.grid_rowconfigure(4, weight=2)  # Extra weight for table section

        # Sample data for the table (mirroring the provided data)
        self.table_data = [
            ["1", "银行存款", "收回维力贸易公司前欠购货款", "52100", ""],
            ["1", "应收账款-维力贸易公司", "收回前欠购货款", "", "52100"],
            ["", "", "合计", "52100", "52100"]
        ]

        # Define system prompts for different AI agents
        self.system_prompts = {
            "agent_1": "You are a financial advisor specializing in banking and loans. Provide detailed advice on financial transactions.",
            "agent_2": "You are a data analyst focused on interpreting financial data and summaries. Provide insights based on numbers and trends.",
            "agent_3": "You are a legal consultant for financial agreements. Provide guidance on contracts and obligations."
        }

        # Create and configure UI elements (Text Areas, Buttons, and Table)
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components like text areas, buttons, and table."""
        # Labels and Text Areas for Input/Output
        self.labels = []
        self.text_areas = []
        for i in range(4):
            # Label for each text area
            label = ttk.Label(self.root, text=f"Text Area {i+1}")
            label.grid(row=i, column=0, padx=5, pady=5, sticky="nw")
            self.labels.append(label)

            # Text Area for input/output
            text_area = tk.Text(self.root, height=5, wrap=tk.WORD)
            text_area.grid(row=i, column=0, padx=5, pady=5, sticky="nsew")
            self.text_areas.append(text_area)

        # Buttons to trigger Cloudflare AI API calls and clear action
        self.buttons = []
        button_configs = [
            ("Ask Financial Advisor (Agent 1)", self.ask_agent_1),
            ("Ask Data Analyst (Agent 2)", self.ask_agent_2),
            ("Ask Legal Consultant (Agent 3)", self.ask_agent_3),
            ("Clear All", self.clear_all)
        ]
        for i, (label, command) in enumerate(button_configs):
            btn = ttk.Button(self.root, text=label, command=command)
            btn.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            self.buttons.append(btn)

        # Set up the table at the bottom of the UI
        self.setup_table()

    def setup_table(self):
        """Set up the table using ttk.Treeview at the bottom of the UI."""
        # Column headers for the table
        headers = ["编号", "科目", "摘要", "借方金额", "贷方金额"]

        # Create a frame for the table and scrollbar
        tree_frame = ttk.Frame(self.root)
        tree_frame.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

        # Create Treeview for the table
        self.tree = ttk.Treeview(tree_frame, columns=headers, show="headings", height=8)
        for header in headers:
            self.tree.heading(header, text=header)
            self.tree.column(header, width=120, anchor=tk.CENTER)  # Adjust width as needed

        # Insert data into Treeview
        for row in self.table_data:
            self.tree.insert("", "end", values=row)

        # Add scrollbars for the table
        tree_scrollbar_y = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        tree_scrollbar_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scrollbar_y.set, xscrollcommand=tree_scrollbar_x.set)

        # Pack the Treeview and scrollbars
        tree_scrollbar_y.pack(side="right", fill="y")
        tree_scrollbar_x.pack(side="bottom", fill="x")
        self.tree.pack(side="left", fill="both", expand=True)

    def ask_agent_1(self):
        """Handle button click for 'Ask Financial Advisor (Agent 1)' (Text Area 1 to Text Area 2)."""
        self.get_cloudflare_response(0, 1, 0, "agent_1")  # Source: Text Area 1, Target: Text Area 2, Button Index: 0

    def ask_agent_2(self):
        """Handle button click for 'Ask Data Analyst (Agent 2)' (Text Area 2 to Text Area 3)."""
        self.get_cloudflare_response(1, 2, 1, "agent_2")  # Source: Text Area 2, Target: Text Area 3, Button Index: 1

    def ask_agent_3(self):
        """Handle button click for 'Ask Legal Consultant (Agent 3)' (Text Area 3 to Text Area 4)."""
        self.get_cloudflare_response(2, 3, 2, "agent_3")  # Source: Text Area 3, Target: Text Area 4, Button Index: 2

    def clear_all(self):
        """Handle button click for 'Clear All' to clear all text areas."""
        for text_area in self.text_areas:
            text_area.delete(1.0, tk.END)

    def get_cloudflare_response(self, source_area_idx, target_area_idx, button_idx, agent_key):
        """
        Fetch response from Cloudflare AI API based on input from source text area
        and display it in target text area, using a specific agent configuration.

        Args:
            source_area_idx (int): Index of source text area for input.
            target_area_idx (int): Index of target text area for output.
            button_idx (int): Index of the button to enable/disable.
            agent_key (str): Key to select the system prompt for the specific agent.
        """
        source_text = self.text_areas[source_area_idx].get(1.0, tk.END).strip()
        if not source_text:
            messagebox.showwarning("Input Error", "Please enter a question!")
            return

        # Disable the button during API call to prevent multiple clicks
        self.buttons[button_idx].config(state="disabled")
        self.text_areas[target_area_idx].delete(1.0, tk.END)
        self.text_areas[target_area_idx].insert(tk.END, "Fetching response...\n")

        # Run API call in a separate thread to prevent UI freezing
        thread = threading.Thread(target=self.fetch_cloudflare_response,
                                 args=(source_text, target_area_idx, button_idx, agent_key))
        thread.daemon = True
        thread.start()

    def fetch_cloudflare_response(self, question, target_area_idx, button_idx, agent_key):
        """
        Fetch response from Cloudflare AI API in a separate thread and update UI.

        Args:
            question (str): The user's question to send to the API.
            target_area_idx (int): Index of target text area for output.
            button_idx (int): Index of the button to enable after response.
            agent_key (str): Key to select the system prompt for the specific agent.
        """
        try:
            # Prepare messages for Cloudflare API with agent-specific system prompt
            messages = [
                {"role": "system", "content": self.system_prompts.get(agent_key, "You are a helpful assistant.")},
                {"role": "user", "content": question}
            ]

            # Make API call to Cloudflare
            response = cloudflare_chat_completion(
                CLOUDFLARE_AUTH_TOKEN,
                CLOUDFLARE_ACCOUNT_ID,
                CLOUDFLARE_MODEL,
                messages
            )

            # Extract the response content if successful, otherwise show error
            if "error" in response:
                answer = f"Error: {response['error']}"
            else:
                # Extract the assistant's reply from the response based on provided structure
                answer = response.get("choices", [{}])[0].get("message", {}).get("content", "No content received")

            # Update UI in the main thread
            self.root.after(0, self.update_text_area, target_area_idx, answer, button_idx)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.root.after(0, self.update_text_area, target_area_idx, error_msg, button_idx)

    def update_text_area(self, target_area_idx, text, button_idx):
        """
        Update the target text area with the response and re-enable the button.

        Args:
            target_area_idx (int): Index of target text area to update.
            text (str): Text to insert into the target text area.
            button_idx (int): Index of the button to re-enable.
        """
        self.text_areas[target_area_idx].delete(1.0, tk.END)
        self.text_areas[target_area_idx].insert(tk.END, text)
        self.buttons[button_idx].config(state="normal")

def main():
    """Main function to run the Tkinter application."""
    root = tk.Tk()
    app = CloudflareChatApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
