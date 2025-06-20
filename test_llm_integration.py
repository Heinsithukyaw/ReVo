#!/usr/bin/env python3
"""
Test script for LLM Integration

This script tests the LLM integration by:
1. Initializing the LLM Manager
2. Getting available models
3. Generating responses
4. Getting health status
"""

import sys
import asyncio
import json
import logging
from datetime import datetime

# Add project paths
sys.path.append('src')
sys.path.append('apps')
sys.path.append('packages')

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_llm_integration")

async def test_llm_manager():
    """Test the LLM Manager functionality."""
    try:
        # Import the LLM Manager
        from src.revoagent.ai.llm_manager import llm_manager
        
        logger.info("LLM Manager imported successfully")
        
        # Initialize the LLM Manager
        logger.info("Initializing LLM Manager...")
        success = await llm_manager.initialize()
        
        if success:
            logger.info("LLM Manager initialized successfully")
        else:
            logger.warning("LLM Manager initialization failed")
        
        # Get available models
        logger.info("Getting available models...")
        models = await llm_manager.get_available_models()
        
        logger.info(f"Found {len(models)} available models:")
        for model in models:
            logger.info(f"  - {model['id']} ({model['source']})")
        
        # Get LLM health status
        logger.info("Getting LLM health status...")
        health = await llm_manager.get_health()
        
        logger.info(f"LLM health status: {health['status']}")
        logger.info(f"Models available: {health['models_available']}")
        
        # Test generation
        test_message = "Write a short poem about artificial intelligence."
        logger.info(f"Testing LLM generation with message: '{test_message}'")
        
        # Choose a model if available
        model = models[0]['id'] if models else None
        
        # Generate a response
        response = await llm_manager.generate_response(test_message, model)
        
        logger.info("Generation successful!")
        logger.info("Generated response:")
        logger.info("---------------------")
        logger.info(response)
        logger.info("---------------------")
        
        # Get updated LLM stats
        logger.info("Getting updated LLM stats...")
        health = await llm_manager.get_health()
        
        logger.info(f"Total requests: {health['stats']['total_requests']}")
        logger.info(f"Successful requests: {health['stats']['successful_requests']}")
        logger.info(f"Average latency: {health['stats']['average_latency']:.2f}s")
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing LLM Manager: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main entry point."""
    logger.info("Starting LLM Integration test...")
    
    # Test LLM Manager
    success = await test_llm_manager()
    
    if success:
        logger.info("LLM Integration test completed successfully!")
    else:
        logger.error("LLM Integration test failed!")
    
if __name__ == "__main__":
    asyncio.run(main())