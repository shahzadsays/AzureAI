import json
import os
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from openai import AzureOpenAI

class Lab3AgentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-102 Lab 3: Agentic Tool Use & ITSM Automation (Azure OpenAI)")
        self.root.geometry("1050x750")
        
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # --- Top Frame: Azure OpenAI Configuration Panel ---
        config_frame = ttk.LabelFrame(root, text=" 1. Azure OpenAI / Foundry Configuration ", padding=10)
        config_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        config_frame.columnconfigure(5, weight=1)

        ttk.Label(config_frame, text="API Key:").grid(row=0, column=0, sticky="w", padx=2)
        self.api_key_entry = ttk.Entry(config_frame, show="*", width=22)
        self.api_key_entry.grid(row=0, column=1, padx=2)
        if os.environ.get("AZURE_OPENAI_API_KEY"):
            self.api_key_entry.insert(0, os.environ.get("AZURE_OPENAI_API_KEY"))

        ttk.Label(config_frame, text="Endpoint URL:").grid(row=0, column=2, sticky="w", padx=2)
        self.endpoint_entry = ttk.Entry(config_frame, width=32)
        self.endpoint_entry.grid(row=0, column=3, padx=2)
        # Pre-populate with your project endpoint if desired
        self.endpoint_entry.insert(0, "https://project-rag-lab2-resource.openai.azure.com/")

        ttk.Label(config_frame, text="Deployment:").grid(row=0, column=4, sticky="w", padx=2)
        self.model_entry = ttk.Entry(config_frame, width=15)
        self.model_entry.insert(0, "gpt-5.4-mini")
        self.model_entry.grid(row=0, column=5, sticky="w", padx=2)

        # --- Middle Frame: Split View (Chat & Execution Logs) ---
        paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        paned_window.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Left Pane: Interactive Chat Interface
        chat_frame = ttk.LabelFrame(paned_window, text=" 2. Service Desk Chat Interface ", padding=10)
        paned_window.add(chat_frame, weight=1)
        
        chat_frame.rowconfigure(0, weight=1)
        chat_frame.columnconfigure(0, weight=1)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, state=tk.DISABLED, width=45, font=("Arial", 10))
        self.chat_display.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

        self.user_input_entry = ttk.Entry(chat_frame, font=("Arial", 10))
        self.user_input_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        self.user_input_entry.bind("<Return>", lambda event: self.send_message())

        send_btn = ttk.Button(chat_frame, text="Send Prompt", command=self.send_message)
        send_btn.grid(row=1, column=1, sticky="ew", padx=5, pady=5)

        # Right Pane: System Execution & Tool Dispatch Logs
        logs_frame = ttk.LabelFrame(paned_window, text=" 3. Backend Tool Execution & JSON Payload Logs ", padding=10)
        paned_window.add(logs_frame, weight=1)
        
        logs_frame.rowconfigure(0, weight=1)
        logs_frame.columnconfigure(0, weight=1)

        self.logs_display = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, state=tk.DISABLED, width=45, font=("Consolas", 9), bg="#1e1e1e", fg="#00ff00")
        self.logs_display.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.reset_conversation_history()

    def reset_conversation_history(self):
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are an enterprise IT Service Desk and Voice Assistant. "
                    "Your job is to securely assist callers with identity verification, "
                    "MFA alerts, and password resets using your available tools. "
                    "Never execute a password reset without first verifying the user's identity."
                )
            }
        ]

    def log_to_console(self, text):
        self.logs_display.config(state=tk.NORMAL)
        self.logs_display.insert(tk.END, text + "\n")
        self.logs_display.see(tk.END)
        self.logs_display.config(state=tk.DISABLED)

    def append_chat(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state=tk.DISABLED)

    # ==========================================
    # BACKEND MOCK FUNCTIONS & JSON SCHEMAS
    # ==========================================
    
    def verify_user_identity(self, employee_id: str, pin_last_four: str) -> str:
        self.log_to_console(f"\n[BACKEND EXECUTION] Database lookup triggered for ID: {employee_id}")
        if employee_id.upper() == "EMP1042" and pin_last_four == "4321":
            return json.dumps({"status": "success", "message": "Identity verified successfully.", "username": "jdoe"})
        return json.dumps({"status": "failure", "message": "Verification failed. Invalid ID or PIN digits."})

    def trigger_mfa_sms(self, phone_number: str, urgency_level: str) -> str:
        self.log_to_console(f"\n[BACKEND EXECUTION] SMS Gateway dispatching token to {phone_number} [Urgency: {urgency_level}]")
        return json.dumps({"status": "success", "message": f"MFA token dispatched securely to {phone_number}."})

    def execute_password_reset(self, ticket_id: str, username: str) -> str:
        self.log_to_console(f"\n[BACKEND EXECUTION] ITSM Webhook calling Active Directory to reset password for '{username}' (Ticket: {ticket_id})")
        return json.dumps({"status": "success", "message": f"Password successfully reset for {username} under ticket {ticket_id}."})

    def get_tool_definitions(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "verify_user_identity",
                    "description": "Verifies employee identity via corporate database using employee ID and last four digits of security PIN.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_id": {"type": "string", "description": "The employee ID, e.g., EMP1042."},
                            "pin_last_four": {"type": "string", "description": "Last four digits of the user's PIN."}
                        },
                        "required": ["employee_id", "pin_last_four"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "trigger_mfa_sms",
                    "description": "Triggers out-of-band SMS containing an MFA security token.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phone_number": {"type": "string", "description": "Destination phone number including country code."},
                            "urgency_level": {"type": "string", "enum": ["low", "medium", "high", "critical"], "description": "Urgency rating."}
                        },
                        "required": ["phone_number", "urgency_level"],
                        "additionalProperties": False
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_password_reset",
                    "description": "Triggers automated password reset workflow tied to an active ITSM ticket.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "ticket_id": {"type": "string", "description": "ITSM ticket number, e.g., INC-88421."},
                            "username": {"type": "string", "description": "System username requiring reset."}
                        },
                        "required": ["ticket_id", "username"],
                        "additionalProperties": False
                    }
                }
            }
        ]

    def send_message(self):
        api_key = self.api_key_entry.get().strip()
        endpoint = self.endpoint_entry.get().strip()
        model_name = self.model_entry.get().strip()
        user_text = self.user_input_entry.get().strip()

        if not api_key or not endpoint:
            messagebox.showerror("Configuration Error", "Please provide both your Azure API Key and Endpoint URL.")
            return
        if not user_text:
            return

        self.user_input_entry.delete(0, tk.END)
        self.append_chat("User", user_text)
        self.messages.append({"role": "user", "content": user_text})

        threading.Thread(target=self.process_agent_turn, args=(api_key, endpoint, model_name), daemon=True).start()

    def process_agent_turn(self, api_key, endpoint, model_name):
        try:
            # Initialize Azure OpenAI Client
            client = AzureOpenAI(
                api_key=api_key,
                azure_endpoint=endpoint,
                api_version="2024-05-01-preview"
            )
            tools = self.get_tool_definitions()

            self.log_to_console(f"\n[API REQUEST] Sending prompt + {len(tools)} tool schemas to Azure deployment '{model_name}'...")

            response = client.chat.completions.create(
                model=model_name,
                messages=self.messages,
                tools=tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            self.messages.append(response_message)

            if response_message.tool_calls:
                self.log_to_console(f"\n[AI DECISION] Model requested {len(response_message.tool_calls)} tool call(s):")
                
                for tool_call in response_message.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args_str = tool_call.function.arguments
                    self.log_to_console(f" -> Function: {fn_name}")
                    self.log_to_console(f" -> Arguments JSON: {fn_args_str}")

                    fn_args = json.loads(fn_args_str)
                    
                    fn_result = ""
                    if fn_name == "verify_user_identity":
                        fn_result = self.verify_user_identity(**fn_args)
                    elif fn_name == "trigger_mfa_sms":
                        fn_result = self.trigger_mfa_sms(**fn_args)
                    elif fn_name == "execute_password_reset":
                        fn_result = self.execute_password_reset(**fn_args)

                    self.log_to_console(f" -> Tool Output Payload: {fn_result}")

                    self.messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": fn_name,
                        "content": fn_result,
                    })

                self.log_to_console("\n[API REQUEST] Submitting tool output payload back to Azure model...")

                second_response = client.chat.completions.create(
                    model=model_name,
                    messages=self.messages
                )
                final_reply = second_response.choices[0].message.content
                self.messages.append(second_response.choices[0])

                self.log_to_console(f"\n[AI RESPONSE SYNTHESIS COMPLETE]")
                self.root.after(0, lambda: self.append_chat("Agent", final_reply))

            else:
                reply = response_message.content
                self.log_to_console("\n[AI RESPONSE] Direct response generated (No tools invoked).")
                self.root.after(0, lambda: self.append_chat("Agent", reply))

        except Exception as e:
            self.log_to_console(f"\n[ERROR] {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Execution Error", str(e)))

if __name__ == "__main__":
    root = tk.Tk()
    app = Lab3AgentApp(root)
    root.mainloop()