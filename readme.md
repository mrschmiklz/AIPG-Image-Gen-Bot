# AI POWER GRID Image Generation Discord Bot

## Overview

This Discord bot is designed to generate images using AI-powered image generation capabilities. It leverages the AI Power Grid API to create images based on user prompts within a Discord server. The bot is built using Python and the nextcord library, offering a seamless integration with Discord's interface.

## Key Features

1. **Image Generation**: Users can generate images by providing text prompts.
2. **Customizable Parameters**: Allows modification of various image generation parameters such as dimensions, steps, CFG scale, and more.
3. **Interactive UI**: Utilizes Discord's button and modal interfaces for a user-friendly experience.
4. **Queue Management**: Implements a queue system to manage API requests efficiently.
5. **Logging**: Comprehensive logging for easier debugging and monitoring.

## Architecture

The bot is structured into several key components:

1. **Main Script** (`main.py`): Initializes the bot and sets up event handlers.
2. **Image Generation Cog** (`cogs/image_generation.py`): Handles image generation commands and user interactions.
3. **Image Generation Utilities** (`image_generation_utils.py`): Contains functions for API interactions.
4. **Queue Manager** (`queue_manager.py`): Manages the queue of API requests to prevent rate limiting.
5. **Configuration** (`config.py`, `constants.py`): Stores bot settings and default parameters.
6. **Logging** (`utils/logger.py`): Provides logging functionality throughout the application.

## Key Components

### Image Generation Process

1. User inputs a prompt using the `!dream` command.
2. The bot sends an initial status message and starts the image generation process.
3. It periodically checks the generation status and updates the status message.
4. Once complete, it retrieves and sends the generated image.
5. Users can then interact with buttons to modify parameters and regenerate images.

### Queue Management

To handle API rate limits, the bot uses a queue system:
- Requests are added to a queue and processed at a controlled rate.
- This ensures compliance with API usage limits and prevents overloading.

### Error Handling

The bot implements robust error handling to manage various scenarios:
- API communication errors
- Invalid user inputs
- Unexpected exceptions

### Customization Options

Users can customize various aspects of image generation:
- Seed
- Dimensions
- Steps
- CFG Scale
- Sampler
- Model

## Flux Image Generation

This bot includes integration with the Flux image generation model, which connects to a local Pinokio server (https://pinokio.computer/). This feature allows for additional image generation capabilities alongside the AI Power Grid API.

Key points about the Flux integration:
- Requires a local Pinokio server running the Flux model
- Accessed through the "Flux it" button in the bot's interface
- Provides an alternative image generation option with different characteristics

To use the Flux integration:
1. Ensure you have a Pinokio server set up and running locally
2. The bot will automatically connect to the Pinokio server at http://127.0.0.1:7860/
3. Use the "Flux it" button in the bot interface to generate images using the Flux model

Note: The Flux integration is an advanced feature and requires additional setup. Make sure your Pinokio server is properly configured before using this feature.

## Setup and Configuration

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file
4. Run the bot: `python main.py`

## Future Enhancements

- Support for multiple AI models
- Advanced prompt engineering features
- Integration with more Discord features (e.g., slash commands)
- User preference saving

## Contributing

Contributions to improve the bot are welcome. Please follow the standard fork-and-pull request workflow.

## License

Per model
