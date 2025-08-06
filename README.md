# Multi-Tool Agent

A versatile agent built with **LangGraph** and powered by **Google's Gemini 2.0 Flash** model. This project automates multi-step tasks such as searching for information and saving results, integrating with external tools to fulfill complex requests.

## Features

- **Wikipedia Search**  
   Search Wikipedia and retrieve concise summaries of topics.

- **Medium Article Reader**  
   Extract the main content from any Medium article via its URL.

- **Google Sheets Integration**  
   Save final answers or summaries directly into a specified Google Sheet.

- **Multi-Step Automation**  
   Chain these tools together to complete requests like "find information and save it."

## Setup and Installation

1. **Clone the repository**

   ```bash
   git clone <git@github.com:emhamza/custom_tool_agent.git>
   cd <custom_tool_agent>
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys and Credentials**

   - Create a `.env` file in the project root and add your `GOOGLE_API_KEY`.
   - Set up the Google Sheets API and generate a `credentials.json` file. Place this file in the project root.
   - Ensure your target Google Sheet is named `automation_agent` and is shared with the service account email from your credentials file.

4. **Run the agent**
   ```bash
   python your_agent_script.py
   ```

## Usage

Interact with the agent via the command line. Provide queries that may require one or more tools to be executed. The agent will automatically select and chain tools as needed.

### Example Queries

- **Search Wikipedia for 'black holes' and save the main points.**
- **Find a tutorial on LangChain multi-agent systems on Medium.**
- **What is a large language model and save the definition.**

Type `exit` or `quit` to end the session.

## Contributing

Contributions are welcome! Please open issues or submit pull requests for improvements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, please open an issue in the repository.
