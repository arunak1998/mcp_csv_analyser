## CSV Analysis Agent with MCP Server

> Transform your CSV files into interactive dashboards and insights using conversational AI

---

## 🚀 Overview

This project demonstrates a powerful **CSV Analysis Agent** built with the **Model Context Protocol (MCP)** that enables natural language querying of CSV data. Simply upload any CSV file, ask questions in plain English, and get instant visualizations and insights through an intelligent dashboard.

---

## ✨ Features

### 🔍 CSV Analysis Agent
- **Natural Language Processing**: Ask questions about your data using everyday language
- **Smart Data Understanding**: Automatically detects column types, patterns, and relationships
- **Statistical Analysis**: Provides descriptive statistics, correlations, and data quality insights
- **Data Cleaning**: Identifies and handles missing values, outliers, and inconsistencies

### 📊 Dashboard Generation Agent
- **Auto-Visualization**: Creates charts, graphs, and plots based on your queries
- **Interactive Dashboards**: Generate comprehensive visual reports instantly
- **Multiple Chart Types**: Bar charts, line graphs, scatter plots, heatmaps, and more
- **Export Options**: Download visualizations and reports in various formats

### 🔧 MCP Server Integration
- **Standardized Protocol**: Uses MCP for seamless AI-tool integration
- **Scalable Architecture**: Handles multiple concurrent requests efficiently
- **Secure Communication**: Built-in authentication and data protection
- **Tool Interoperability**: Compatible with various AI clients and applications

---

## 🛠️ Technology Stack

- **Backend**: Python with FastMCP
- **AI Framework**: LangChain for intelligent agent orchestration
- **Frontend**: Streamlit for interactive web interface
- **Protocol**: Model Context Protocol (MCP) for standardized AI integration
- **Visualization**: Plotly, Matplotlib, Seaborn for dynamic charts

---

## 📁 Project Structure

csv-analysis-agent/
├── server/
│ ├── app.py # streamlit
│ ├── csv_agent.py # CSV analysis logic
│ ├── dashboard_agent.py # Dashboard generation logic
├── config.yaml
└── README.md

text

---

## ⚡ Quick Start

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. **Clone the repository**
git clone https://github.com/yourusername/csv-analysis-agent.git
cd csv-analysis-agent

text

2. **Clone the MCP Server (Private Repository)**
git clone https://github.com/yourusername/your-mcp-server.git
cd your-mcp-server

text

3. **Install dependencies**
pip install -e .

text
> Uses `pyproject.toml` for modern Python dependency management

4. **Start the MCP Server**
FILE_LOCATION="/mnt/c/workspaces/mcpserver/temp/*.csv" python server/analyst.py

text
> The server will be hosted as SSE (Server-Sent Events) for real-time communication

5. **Launch the Streamlit Dashboard**
streamlit run server/app.py

text

6. **Access the application**
Open your browser and navigate to `http://localhost:8501`

## 🎯 Usage

### Upload and Analyze

1. **Upload CSV File**: Drag and drop or browse to select your CSV file
2. **Ask Questions**: Use natural language to query your data
- "What are the top 5 products by sales?"
- "Show me the trend of revenue over time"
- "Create a dashboard for customer demographics"
3. **Get Instant Results**: View generated visualizations and insights

### Example Queries

📊 "Create a sales performance dashboard"
📈 "Show correlation between price and sales volume"
🔍 "What are the key trends in my data?"
📋 "Generate a summary report of all metrics"
🎯 "Find outliers in customer spending patterns"

text

---

## 🔧 Configuration



### Environment Variables

Create a `.env` file:
FILE_LOCATION=path/to/default/csv/directory

OPENAI_API_KEY=your_api_key_here # Optional: for enhanced AI capabilities

text

---

## 🏗️ Architecture

### MCP Server Components
- **CSV Agent**: Handles data loading, cleaning, and analysis
- **Dashboard Agent**: Manages visualization generation and layout


### Client Interface
- **Streamlit App**: User-friendly web interface
- **Real-time Updates**: Live data streaming via SSE
- **Interactive Elements**: Dynamic filters, drill-downs, and exports

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request





## 🙋‍♂️ Support

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/yourusername/csv-analysis-agent/issues)


---

## 🎉 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io) for the standardized AI integration framework
- [Streamlit](https://streamlit.io) for the amazing web app framework
- [LangChain](https://langchain.com) for powerful AI agent capabilities

---

**Built with ❤️ using MCP, Python, and AI**
Transform your data analysis workflow from manual spreadsheet work to conversational AI insights in minutes, not hours.