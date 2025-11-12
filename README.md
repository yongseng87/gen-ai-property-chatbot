# Property Agent Chatbot

## Description

This repository contains the architecture and deployment of a real-estate chatbot which handles user queries and serves as an aid to property agents. User queries are classified into one of three categories: lease term queries, property statistical queries, or general queries. The queries are then processed by the chatbot. The architecture overview is shown in the following diagram:


![Model Architecture](architecture.png)


Other than the main chatbot page, the deployed website also contains a property statistics page, which provides users with clear visualizations of the property database stored in the model. User can interactively filter the properties by different features and view their statistics. 


![Property Statistics Page](statistics.png)


## Getting Started

### Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yongseng87/gen-ai-property-chatbot.git
   ```

2. Navigate to the repository folder:
   ```bash
   cd gen-ai-property-chatbot
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Launch Webpage

```python
streamlit run streamlit_trial.py
```

## Credit

* Lim Kai Xiang 
* Quek Yong Seng
* Wen Qianyi (Vivian)
* Zhang Jiasheng