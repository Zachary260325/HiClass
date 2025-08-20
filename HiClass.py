from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.messages import TextMessage, UserMessage
import json
import os
from dotenv import load_dotenv
from prompt import PROMPTS

import asyncio
import warnings


class HiClass:
    def __init__(self):
        self.model_client = None
        self._connect_to_agent()
    
    def _connect_to_agent(self):
        load_dotenv()
        api_key = os.getenv("LLM_API_KEY")
        base_url = os.getenv("LLM_BASE_URL")
        if api_key is None or base_url is None:
            raise ValueError("LLM_API_KEY or LLM_BASE_URL is not set")
        
        self.model_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            base_url=base_url,
            api_key=api_key,
            max_tokens=4096,
        )

    def _read_json_file(self, file_path):
        with open(file_path, "r") as f:
            return json.load(f)

    def extract_all_headers(self, json_data):
        
        headers = []
        
        for page in json_data:
            page_no = page.get("page_no", 0)
            layout_info = page.get("full_layout_info", [])

            for box in layout_info:
                box_type = box.get("category", "")  # Changed from 'type' to 'category'
                text = box.get("text", "")
                bbox = box.get("bbox", [])

                if box_type in ["Title", "Section-header"]:
                    headers.append(text.strip())

        return headers
    
    def _previous_structure_to_str(self, previous_structure):
        # Convert the previous structure to a markdown string
        md_lines = ["Section Title (str): Level (int)"]
        for (title, level) in previous_structure:
            md_lines.append(f"'{title}': {level}")
        return "\n".join(md_lines)

    async def query_header_level(self, previous_structure, suggested_level, current_header, max_retries=3):
        # Ask LLM to give only an integer of the current header's level, with retries
        headings = self._previous_structure_to_str(previous_structure)
        # print(f"Current hierarchy structure:\n{headings}\nNew header to classify: {current_header}")
        print(f"Classifying: {current_header}")
        prompt = PROMPTS["Level_Extraction_Prompt"].format(
            hierarchy_structure=headings,
            suggested_level=suggested_level,
            new_header=current_header
        )
        for attempt in range(max_retries):
            response = await self.model_client.create(
                messages=[
                    UserMessage(content=prompt, source="System")
                ]
            )
            
            # print(f"Attempt {attempt + 1}: {response}")
            
            # Dictionary response structure
            content = response.content
            
            # validate if could be parsed as int
            return int(content.strip())

        raise ValueError("Failed to determine header level after multiple attempts")

    async def extract_header_levels(self, json_data):
        headers = self.extract_all_headers(json_data)
        header_levels = []
        MAX_LEVEL = 6

        for header in headers:
            level = MAX_LEVEL  # Default level
            if header.startswith("#"):
                level = len(header) - len(header.lstrip("#"))
                header = header.lstrip("#").strip()

            try:
                query_level = await self.query_header_level(header_levels, level, header)
            except ValueError as e:
                query_level = level
                print(f"Warning: Failed to determine level for header '{header}'. Using default level {level}. Error: {e}")
                warnings.warn(f"Failed to determine level for header: {header}. Using default level {level}. Error: {e}")
            header_levels.append((header.strip(), query_level))

        return header_levels
    
    async def extract_ToC(self, json_path):
        json_data = self._read_json_file(json_path)
        header_levels = await self.extract_header_levels(json_data)

        toc = []
        for (header, level) in header_levels:
            toc.append({"title": header, "level": level})

        return toc

    def save_ToC(self, toc, file_path, file_name):
        # create path if not exists
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        with open(os.path.join(file_path, file_name), "w") as f:
            json.dump(toc, f, indent=2)
            
    def ToC_to_md(self, toc):
        md_lines = []
        for item in toc:
            level, title = item["level"], item["title"]
            md_lines.append(f"{'#' * level} {title}")
        return "\n".join(md_lines)

async def main():
    hi_class = HiClass()
    file_name = "PGhandbook2025"
    toc = await hi_class.extract_ToC(f"./test_files/{file_name}.json")
    hi_class.save_ToC(toc, "./toc", f"{file_name}_toc.json")
    
    print(hi_class.ToC_to_md(toc))

if __name__ == "__main__":
    asyncio.run(main())