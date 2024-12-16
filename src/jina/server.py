from typing import Any, Optional
import asyncio
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import logging
from logging.handlers import RotatingFileHandler
import os
import json
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key
JINA_API_KEY = os.getenv("JINA_API_KEY")

# Create logs directory
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# File handler
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'jina_reader.log'),
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Add handlers
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Remove default handlers from root logger
logging.getLogger().handlers = []

# Initialize server
server = Server("jina-reader")

# Tool list handler
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return [
        types.Tool(
            name="read-webpage",
            description="Convert webpage content to LLM-friendly format",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the webpage to read",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["markdown", "html", "text", "screenshot"],
                        "default": "markdown",
                        "description": "Output format",
                    },
                    "generate_alt": {
                        "type": "boolean",
                        "default": False,
                        "description": "Generate alt text for images",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds",
                    },
                    "selector": {
                        "type": "string",
                        "description": "CSS selector",
                    },
                    "wait_for": {
                        "type": "string",
                        "description": "Wait for specific element",
                    },
                    "proxy": {
                        "type": "string",
                        "description": "Proxy server URL",
                    },
                },
                "required": ["url"],
            },
        ),
        # Add search tool
        types.Tool(
            name="web-search",
            description="Search web and return results in LLM-friendly format",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query",
                    },
                    "site": {
                        "type": "string",
                        "description": "Limit search to specific domain",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5,
                        "minimum": 1,
                        "maximum": 10,
                    },
                    "retain_images": {
                        "type": "boolean",
                        "description": "Whether to retain images",
                        "default": True,
                    },
                },
                "required": ["query"],
            },
        ),
    ]

# In server initialization, add list_prompts handler
@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """List available prompts"""
    return [
        types.Prompt(
            name="fetch",
            description="Get webpage content and convert to markdown format",
            arguments=[
                types.PromptArgument(
                    name="url",
                    description="URL of the webpage to fetch",
                    required=True
                )
            ],
        ),
        types.Prompt(
            name="search",
            description="Search web and return LLM-friendly results",
            arguments=[
                types.PromptArgument(
                    name="query",
                    description="Search query",
                    required=True
                ),
                types.PromptArgument(
                    name="site",
                    description="Limit search to specific domain",
                    required=False
                ),
            ],
        )
    ]

async def format_search_results(data: list, max_results: int = 5) -> str:
    """Format search results"""
    if not data:
        return "No search results found."
        
    formatted_results = []
    for idx, item in enumerate(data[:max_results], 1):
        logger.debug(f"Processing result {idx}: {item.get('url')}")
        formatted_results.append(f"### Result {idx}\n")
        formatted_results.append(f"URL: {item.get('url', 'N/A')}\n")
        formatted_results.append(f"Title: {item.get('title', 'N/A')}\n")
        formatted_results.append(f"Content:\n{item.get('content', 'N/A')}\n")
        formatted_results.append("---\n")
    
    return "\n".join(formatted_results)

@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
    """Get prompt content"""
    logger.debug(f"Getting prompt: {name}")
    logger.debug(f"Arguments: {arguments}")
    
    if not arguments:
        raise ValueError("Missing arguments")

    if name == "fetch":
        if "url" not in arguments:
            raise ValueError("Missing URL parameter")

        url = arguments["url"]
        try:
            result = await fetch_content(url)
            data = result.get('data', {})
            content = data.get('content', '')
            title = data.get('title', '')
            
            if title:
                content = f"# {title}\n\n{content}"
                
            return types.GetPromptResult(
                description=f"Contents of {url}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=content
                        )
                    )
                ],
            )
        except Exception as e:
            return types.GetPromptResult(
                description=f"Failed to fetch {url}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Error: {str(e)}"
                        )
                    )
                ],
            )
    elif name == "search":
        if "query" not in arguments:
            raise ValueError("Missing query parameter")

        try:
            # Reuse search functionality from handle_call_tool
            results = await handle_call_tool("web-search", arguments)
            content = results[0].text if results else "No results found."
            
            return types.GetPromptResult(
                description=f"Search results for: {arguments['query']}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=content
                        )
                    )
                ],
            )
        except Exception as e:
            return types.GetPromptResult(
                description=f"Error searching for: {arguments['query']}",
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"Error: {str(e)}"
                        )
                    )
                ],
            )
    else:
        raise ValueError(f"Unknown prompt: {name}")

async def fetch_content(url: str, **kwargs) -> dict:
    """Fetch content from r.jina.ai"""
    logger.debug(f"fetch_content called with url: {url}")
    logger.debug(f"kwargs: {kwargs}")
    
    headers = {
        "Accept": "application/json",
        "x-respond-with": kwargs.get("format", "markdown"),
    }
    
    if kwargs.get("generate_alt"):
        headers["x-with-generated-alt"] = "true"
    if kwargs.get("timeout"):
        headers["x-timeout"] = str(kwargs["timeout"])
    if kwargs.get("selector"):
        headers["x-target-selector"] = kwargs["selector"]
    if kwargs.get("wait_for"):
        headers["x-wait-for-selector"] = kwargs["wait_for"]
    if kwargs.get("proxy"):
        headers["x-proxy-url"] = kwargs["proxy"]

    logger.debug(f"Request headers: {headers}")

    async with httpx.AsyncClient() as client:
        try:
            full_url = f"https://r.jina.ai/{url}"
            logger.debug(f"Making request to: {full_url}")
            
            response = await client.get(
                full_url,
                headers=headers,
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Response: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in fetch_content: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to fetch content: {str(e)}")

# Change get_resource to read_resource
@server.read_resource()
async def handle_read_resource(
    uri: str,
    arguments: dict | None = None,
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Read resource content"""
    logger.debug(f"Reading resource: {uri}")
    
    uri_str = str(uri)
    try:
        from urllib.parse import urlparse, unquote
        parsed = urlparse(uri_str)
        
        if not parsed.scheme == "webpage":
            raise ValueError(f"Unsupported scheme: {parsed.scheme}")
            
        # Process templated URL
        if parsed.path.startswith("/content/"):
            # Extract encoded URL from path
            encoded_url = parsed.path[9:]  # Skip "/content/"
            url = unquote(encoded_url)
        else:
            # Process static resources
            url = "https://docs.jina.ai"
            
        # Get content
        result = await fetch_content(url)
        data = result.get('data', {})
        
        # Return resource content list
        return [
            types.TextContent(
                type="text",
                mimeType="text/markdown",
                text=data.get('content', ''),
                metadata={
                    "title": data.get('title', ''),
                    "description": data.get('description', ''),
                    "url": url,
                }
            )
        ]
        
    except Exception as e:
        logger.error(f"Error reading resource: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to read resource: {str(e)}")

async def search_web(query: str, site: str = None, retain_images: bool = True, **kwargs) -> dict:
    """Search web using s.jina.ai"""
    logger.debug(f"Searching web for: {query}")
    logger.debug(f"Site filter: {site}")
    logger.debug(f"Retain images: {retain_images}")
    logger.debug(f"JINA_API_KEY: {JINA_API_KEY}")
    
    if not JINA_API_KEY:
        raise ValueError("JINA_API_KEY not found in environment variables")
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {JINA_API_KEY}"
    }
    
    # If images are not retained, add corresponding header
    if not retain_images:
        headers["X-Retain-Images"] = "none"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            from urllib.parse import quote, urlencode
            
            # Build base URL
            encoded_query = quote(query)
            url = f"https://s.jina.ai/{encoded_query}"
            
            # Add site parameter (if any)
            if site:
                params = {"site": site}
                url = f"{url}?{urlencode(params)}"
            
            logger.debug(f"Making request to: {url}")
            logger.debug(f"Request headers: {headers}")
            
            response = await client.get(
                url,
                headers=headers,
            )
            response.raise_for_status()
            
            result = response.json()
            logger.debug(f"Search response: {result}")
            return result
            
        except httpx.TimeoutException as e:
            logger.error(f"Request timed out: {e}", exc_info=True)
            raise ValueError(f"Search request timed out after 30 seconds")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error("Unauthorized: Invalid API key")
                raise ValueError("Invalid API key")
            elif e.response.status_code == 403:
                logger.error("Forbidden: Access denied")
                raise ValueError("Access denied")
            else:
                logger.error(f"HTTP error occurred: {e}", exc_info=True)
                raise ValueError(f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Error in search_web: {str(e)}", exc_info=True)
            raise ValueError(f"Failed to search web: {str(e)}")

@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool call"""
    logger.debug(f"handle_call_tool called with name: {name}")
    logger.debug(f"arguments: {arguments}")
    
    if not arguments:
        raise ValueError("Missing arguments")

    if name == "read-webpage":
        url = arguments.get("url")
        logger.debug(f"URL from arguments: {url}")
        
        if not url:
            raise ValueError("Missing URL parameter")
        
        try:
            kwargs = arguments.copy()
            kwargs.pop('url', None)
            logger.debug(f"Cleaned kwargs: {kwargs}")
            
            result = await fetch_content(url, **kwargs)
            
            content = result.get('data', {}).get('content', '')
            title = result.get('data', {}).get('title', '')
            
            if title:
                content = f"# {title}\n\n{content}"
            
            return [
                types.TextContent(
                    type="text",
                    text=content
                )
            ]
            
        except Exception as e:
            logger.error(f"Error in handle_call_tool: {str(e)}", exc_info=True)
            return [
                types.TextContent(
                    type="text", 
                    text=f"Error processing webpage: {str(e)}"
                )
            ]
    elif name == "web-search":
        logger.debug("Handling web-search tool call")
        query = arguments.get("query")
        site = arguments.get("site")
        retain_images = arguments.get("retain_images", True)
        max_results = min(arguments.get("max_results", 5), 10)
        
        logger.debug(f"Search query: {query}")
        logger.debug(f"Site filter: {site}")
        logger.debug(f"Retain images: {retain_images}")
        logger.debug(f"Max results: {max_results}")
        
        if not query:
            logger.error("Missing query parameter")
            raise ValueError("Missing query parameter")
        
        try:
            logger.info(f"Starting web search for query: {query}")
            result = await search_web(query, site=site, retain_images=retain_images)
            logger.debug(f"Raw search result: {result}")
            
            data = result.get('data', [])
            logger.info(f"Found {len(data)} search results")
            
            if not data:
                logger.warning("No search results found")
                return [
                    types.TextContent(
                        type="text",
                        text="No search results found for the query."
                    )
                ]
            
            # Format search results
            formatted_results = []
            for idx, item in enumerate(data[:max_results], 1):
                logger.debug(f"Processing result {idx}: {item.get('url')}")
                formatted_results.append(f"### Result {idx}\n")
                formatted_results.append(f"URL: {item.get('url', 'N/A')}\n")
                formatted_results.append(f"Title: {item.get('title', 'N/A')}\n")
                formatted_results.append(f"Content:\n{item.get('content', 'N/A')}\n")
                formatted_results.append("---\n")
            
            final_text = "\n".join(formatted_results)
            logger.debug(f"Final formatted text length: {len(final_text)}")
            
            return [
                types.TextContent(
                    type="text",
                    text=final_text
                )
            ]
            
        except Exception as e:
            logger.error(f"Error in web search: {str(e)}", exc_info=True)
            logger.error(f"Full arguments: {arguments}")
            return [
                types.TextContent(
                    type="text", 
                    text=f"Error searching web: {str(e)}"
                )
            ]
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    """Run the server"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="jina-reader",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
