import sys
import httpx
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
import requests
import logging

load_dotenv()



name = "Tools"
logging.basicConfig(
    level = logging.INFO,
    format = '%(asctime)s %(levelname)s - %(message)s',
    handlers = [logging.StreamHandler()]
)
logger = logging.getLogger(name)

mcp = FastMCP('Tools')

@mcp.tool()
async def get_news_tool(country: str):
    async with httpx.AsyncClient() as client:
        url = f"https://newsdata.io/api/1/latest?apikey={os.getenv('NEWS_API')}&country={country}&language=en"
        response = await client.get(url)
        return response.json()


@mcp.tool()
async def get_stock_price_tool(symbol:str):
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={os.getenv('ALPHA_VANTAGE_API_KEY')}"
    ans = await requests.get(url)
    return ans.json()

def main():
    # Initialize and run the server
    print(get_news_tool('ind'))
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()