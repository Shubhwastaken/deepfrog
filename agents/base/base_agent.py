from abc import ABC, abstractmethod
import logging

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
        self.logger = logging.getLogger(name)

    @abstractmethod
    async def run(self, input_data: dict) -> dict:
        pass

    def log(self, msg: str):
        self.logger.info(msg)
