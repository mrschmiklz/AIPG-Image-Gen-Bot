import nextcord
from nextcord.ext import commands
from nextcord import ButtonStyle, Interaction
from nextcord.ui import Button, View, Modal, TextInput, Select
import asyncio
import time
import random
from config import CHANNEL_ID
from utils.logger import info, error, debug
from image_generation_utils import generate_image_queued, check_image_status_queued, retrieve_generated_image_queued, download_image
from constants import MAX_WAIT_TIME, CHECK_INTERVAL, DEFAULT_IMAGE_PARAMS
from copy import deepcopy
import copy
import json
from requests.exceptions import HTTPError
import subprocess
from gradio_client import Client
import os
import traceback
from queue_manager import flux_queue_manager

class SeedInputModal(nextcord.ui.Modal):
    def __init__(self, view, current_seed):
        super().__init__(title="Change Seed")
        self.view = view
        
        self.seed_input = nextcord.ui.TextInput(
            label="New Seed (-1 for random)",
            placeholder="Enter a new seed or -1 for random",
            default_value=str(current_seed)
        )
        self.add_item(self.seed_input)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        new_seed = self.seed_input.value
        new_params = copy.deepcopy(self.view.original_params)
        if new_seed == "-1":
            new_seed = str(random.randint(0, 4294967295))
        new_params['params']['seed'] = new_seed
        debug(f"SeedInputModal: New seed set to {new_seed}")
        await self.view.cog.generate_and_send_image(interaction, self.view.prompt, new_params)
        await interaction.followup.send(f"Generating image with new seed: {new_seed}", ephemeral=True)

class DimensionsInputModal(nextcord.ui.Modal):
    def __init__(self, view, current_width, current_height):
        super().__init__(title="Change Dimensions")
        self.view = view
        
        self.width_input = nextcord.ui.TextInput(
            label="Width (512-1280)",
            placeholder="Enter width between 512 and 1280",
            default_value=str(current_width),
            min_length=3,
            max_length=4
        )
        self.add_item(self.width_input)

        self.height_input = nextcord.ui.TextInput(
            label="Height (512-1280)",
            placeholder="Enter height between 512 and 1280",
            default_value=str(current_height),
            min_length=3,
            max_length=4
        )
        self.add_item(self.height_input)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            new_width = int(self.width_input.value)
            new_height = int(self.height_input.value)
            
            if 512 <= new_width <= 1280 and 512 <= new_height <= 1280:
                new_params = copy.deepcopy(self.view.original_params)
                new_params['params']['width'] = new_width
                new_params['params']['height'] = new_height
                debug(f"New dimensions set: {new_width}x{new_height}")
                await self.view.cog.generate_and_send_image(interaction, self.view.prompt, new_params)
                await interaction.followup.send(f"Generating image with new dimensions: {new_width}x{new_height}", ephemeral=True)
            else:
                await interaction.followup.send("Invalid dimensions. Please enter values between 512 and 1280.", ephemeral=True)
        except ValueError:
            await interaction.followup.send("Invalid input. Please enter numeric values only.", ephemeral=True)

class StepsInputModal(nextcord.ui.Modal):
    def __init__(self, view, current_steps):
        super().__init__(title="Change Steps")
        self.view = view
        
        self.steps_input = nextcord.ui.TextInput(
            label="Steps (10-150)",
            placeholder="Enter steps between 10 and 150",
            default_value=str(current_steps),
            min_length=1,
            max_length=3
        )
        self.add_item(self.steps_input)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            new_steps = int(self.steps_input.value)
            
            if 10 <= new_steps <= 150:
                new_params = copy.deepcopy(self.view.original_params)
                new_params['params']['steps'] = new_steps
                debug(f"New steps set: {new_steps}")
                await self.view.cog.generate_and_send_image(interaction, self.view.prompt, new_params)
                await interaction.followup.send(f"Generating image with new steps: {new_steps}", ephemeral=True)
            else:
                await interaction.followup.send("Invalid steps. Please enter a value between 10 and 150.", ephemeral=True)
        except ValueError:
            await interaction.followup.send("Invalid input. Please enter a numeric value only.", ephemeral=True)

class CFGScaleInputModal(nextcord.ui.Modal):
    def __init__(self, view, current_cfg_scale):
        super().__init__(title="Change CFG Scale")
        self.view = view
        
        self.cfg_scale_input = nextcord.ui.TextInput(
            label="CFG Scale (1-30)",
            placeholder="Enter CFG scale between 1 and 30",
            default_value=str(current_cfg_scale),
            min_length=1,
            max_length=4
        )
        self.add_item(self.cfg_scale_input)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            new_cfg_scale = float(self.cfg_scale_input.value)
            
            if 1 <= new_cfg_scale <= 30:
                new_params = copy.deepcopy(self.view.original_params)
                new_params['params']['cfg_scale'] = new_cfg_scale
                debug(f"New CFG scale set: {new_cfg_scale}")
                await self.view.cog.generate_and_send_image(interaction, self.view.prompt, new_params)
                await interaction.followup.send(f"Generating image with new CFG scale: {new_cfg_scale}", ephemeral=True)
            else:
                await interaction.followup.send("Invalid CFG scale. Please enter a value between 1 and 30.", ephemeral=True)
        except ValueError:
            await interaction.followup.send("Invalid input. Please enter a numeric value only.", ephemeral=True)

class SamplerSelectionView(nextcord.ui.View):
    def __init__(self, original_view, current_sampler):
        super().__init__(timeout=None)
        self.original_view = original_view
        
        self.sampler_select = nextcord.ui.Select(
            placeholder="Select a sampler",
            options=[
                nextcord.SelectOption(label=sampler, value=sampler, default=(sampler == current_sampler))
                for sampler in [
                    "k_euler_a", "k_dpm_fast", "k_euler", "k_dpm_2_a", "k_heun", "lcm",
                    "k_dpmpp_2m", "k_dpmpp_2s_a", "k_dpm_adaptive", "k_dpmpp_sde",
                    "dpmsolver", "k_dpm_2", "k_lms", "DDIM"
                ]
            ]
        )
        self.sampler_select.callback = self.sampler_callback
        self.add_item(self.sampler_select)

    async def sampler_callback(self, interaction: nextcord.Interaction):
        new_sampler = self.sampler_select.values[0]
        new_params = copy.deepcopy(self.original_view.original_params)
        new_params['params']['sampler_name'] = new_sampler
        debug(f"SamplerSelectionView: New sampler set to {new_sampler}")
        await self.original_view.cog.generate_and_send_image(interaction, self.original_view.prompt, new_params)
        await interaction.message.delete()

class ModelSelectionView(nextcord.ui.View):
    def __init__(self, cog, original_view, current_model):
        super().__init__(timeout=None)
        self.cog = cog
        self.original_view = original_view
        self.add_item(ModelDropdown(cog, original_view, current_model))

class ModelDropdown(nextcord.ui.Select):
    def __init__(self, cog, original_view, current_model):
        self.cog = cog
        self.original_view = original_view
        options = [nextcord.SelectOption(label=model, value=model, default=(model == current_model)) 
                   for model in cog.available_models]
        super().__init__(placeholder="Select a model", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        new_model = self.values[0]
        new_params = copy.deepcopy(self.original_view.original_params)
        new_params['models'] = [new_model]
        debug(f"ModelDropdown: New model set to {new_model}")
        await self.cog.generate_and_send_image(interaction, self.original_view.prompt, new_params)
        await interaction.followup.send(f"Generating image with new model: {new_model}", ephemeral=True)
        await interaction.message.delete()

class ManualCheckView(nextcord.ui.View):
    def __init__(self, cog, job_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.job_id = job_id

    @nextcord.ui.button(label="Check Status", style=ButtonStyle.primary, custom_id="check_status")
    async def check_status_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        await self.cog.check_generation_status(interaction, self.job_id)

class ImageGenerationView(nextcord.ui.View):
    def __init__(self, cog, prompt, params):
        super().__init__(timeout=None)
        self.cog = cog
        self.prompt = prompt
        self.original_params = copy.deepcopy(params)
        debug(f"ImageGenerationView initialized with prompt: {prompt}")
        debug(f"Original params: {json.dumps(self.original_params, indent=2)}")

    @nextcord.ui.button(label="Refresh", style=ButtonStyle.primary, custom_id="refresh")
    async def refresh_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Refresh button clicked")
        await interaction.response.defer()
        new_params = copy.deepcopy(self.original_params)
        new_params['params']['seed'] = str(random.randint(0, 4294967295))
        debug(f"New seed for refresh: {new_params['params']['seed']}")
        await self.cog.generate_and_send_image(interaction, self.prompt, new_params)

    @nextcord.ui.button(label="Change Seed", style=ButtonStyle.secondary, custom_id="change_seed")
    async def change_seed_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Change Seed button clicked")
        current_seed = self.original_params['params']['seed']
        modal = SeedInputModal(self, current_seed)
        await interaction.response.send_modal(modal)

    @nextcord.ui.button(label="Change Dimensions", style=ButtonStyle.secondary, custom_id="change_dimensions")
    async def change_dimensions_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Change Dimensions button clicked")
        current_width = self.original_params['params']['width']
        current_height = self.original_params['params']['height']
        modal = DimensionsInputModal(self, current_width, current_height)
        await interaction.response.send_modal(modal)

    @nextcord.ui.button(label="Change Steps", style=ButtonStyle.secondary, custom_id="change_steps")
    async def change_steps_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Change Steps button clicked")
        current_steps = self.original_params['params']['steps']
        modal = StepsInputModal(self, current_steps)
        await interaction.response.send_modal(modal)

    @nextcord.ui.button(label="Change CFG Scale", style=ButtonStyle.secondary, custom_id="change_cfg_scale")
    async def change_cfg_scale_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Change CFG Scale button clicked")
        current_cfg_scale = self.original_params['params']['cfg_scale']
        modal = CFGScaleInputModal(self, current_cfg_scale)
        await interaction.response.send_modal(modal)

    @nextcord.ui.button(label="Change Sampler", style=ButtonStyle.secondary, custom_id="change_sampler")
    async def change_sampler_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Change Sampler button clicked")
        current_sampler = self.original_params['params']['sampler_name']
        view = SamplerSelectionView(self, current_sampler)
        await interaction.response.send_message("Select a new sampler:", view=view, ephemeral=True)

    @nextcord.ui.button(label="Change Model", style=ButtonStyle.secondary, custom_id="change_model")
    async def change_model_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Change Model button clicked")
        current_model = self.original_params['models'][0]
        view = ModelSelectionView(self.cog, self, current_model)
        await interaction.response.send_message("Select a new model:", view=view, ephemeral=True)

    @nextcord.ui.button(label="Change Prompt", style=ButtonStyle.secondary, custom_id="change_prompt")
    async def change_prompt_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Change Prompt button clicked")
        await interaction.response.send_modal(PromptInputModal(self))

    @nextcord.ui.button(label="Flux it", style=ButtonStyle.success, custom_id="flux_it")
    async def flux_it_callback(self, button: nextcord.ui.Button, interaction: Interaction):
        debug("Flux it button clicked")
        await interaction.response.defer(ephemeral=True)
        try:
            # Run the Flux generation in a separate task
            self.bot.loop.create_task(self.generate_flux_image(interaction, self.prompt))
            await interaction.followup.send("Flux image generation started. Please wait...", ephemeral=True)
        except Exception as e:
            error(f"Error in flux_it_callback: {str(e)}")
            await interaction.followup.send("An error occurred while starting Flux image generation. Please try again later.", ephemeral=True)

    async def generate_flux_image(self, interaction: Interaction, prompt: str):
        async def flux_task():
            try:
                debug(f"Starting Flux image generation for prompt: {prompt}")
                client = Client("http://127.0.0.1:7860/")
                debug("Flux API client initialized")
                result = await asyncio.to_thread(client.predict,
                    prompt,
                    "black-forest-labs/FLUX.1-schnell",
                    random.randint(0, 2**32 - 1),
                    0,
                    1,
                    True,
                    1024,
                    576,
                    4,
                    api_name="/infer"
                )
                debug(f"Flux API response received: {result}")
                
                if not result or len(result) < 2 or not result[0]:
                    raise ValueError("Unexpected result format from Flux API")

                image_path = result[0][0]['image']
                seed = result[1]
                
                if not os.path.exists(image_path):
                    raise FileNotFoundError(f"Generated image not found at {image_path}")

                file = nextcord.File(image_path, filename="flux_image.png")
                embed = nextcord.Embed(title="Flux Image Generated", description=f"Prompt: {prompt}", color=0x00ff00)
                embed.set_image(url="attachment://flux_image.png")
                embed.add_field(name="Seed", value=str(seed), inline=False)
                
                await interaction.followup.send(embed=embed, file=file)
            except Exception as e:
                error(f"Error generating Flux image: {str(e)}")
                error(f"Traceback: {traceback.format_exc()}")
                await interaction.followup.send(f"An error occurred while generating the Flux image: {str(e)}", ephemeral=True)

        try:
            await flux_queue_manager.run_coroutine(flux_task())
        except Exception as e:
            error(f"Error in Flux queue: {str(e)}")
            error(f"Traceback: {traceback.format_exc()}")
            await interaction.followup.send("An error occurred while queuing the Flux image generation. Please try again later.", ephemeral=True)

class PromptInputModal(nextcord.ui.Modal):
    def __init__(self, view):
        super().__init__(title="Change Prompt")
        self.view = view
        
        self.prompt_input = nextcord.ui.TextInput(
            label="New Prompt",
            placeholder="Enter a new prompt",
            default_value=self.view.prompt,
            max_length=1000
        )
        self.add_item(self.prompt_input)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        new_prompt = self.prompt_input.value
        debug(f"PromptInputModal: New prompt set to {new_prompt}")
        await self.view.cog.generate_and_send_image(interaction, new_prompt, self.view.original_params)
        await interaction.followup.send("Generating image with new prompt...", ephemeral=True)

class ImageGeneration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.available_models = []
        self.bot.loop.create_task(self.initialize_models())
        self.channel_id = int(CHANNEL_ID)
        info(f"ImageGeneration cog initialized with channel ID: {self.channel_id}")

    async def initialize_models(self):
        self.available_models = await self.get_available_models()

    @commands.command(name="dream")
    async def dream_command(self, ctx, *, prompt):
        if ctx.channel.id != self.channel_id:
            return
        await self.generate_and_send_image(ctx.channel, prompt)

    @commands.command(name="list_models")
    async def list_models_command(self, ctx):
        if ctx.channel.id != self.channel_id:
            return
        """Command to list available models"""
        await ctx.send("Fetching available models...")
        try:
            models = await self.get_available_models()
            if models:
                model_list = "\n".join(models)
                await ctx.send(f"Available models:\n```\n{model_list}\n```")
            else:
                await ctx.send("No models found or an error occurred while fetching models.")
        except Exception as e:
            error_message = f"An error occurred while fetching models: {str(e)}"
            error(error_message)
            await ctx.send(error_message)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        if message.channel.id != self.channel_id:
            return
        
        if message.content.startswith('!dream'):
            await self.handle_dream_command(message)

    async def handle_dream_command(self, message):
        info(f"Handling dream command: {message.content}")
        prompt = message.content[7:].strip()  # Remove '!dream ' from the start

        if not prompt:
            await message.channel.send("Please provide a prompt after the !dream command.")
            return

        await self.generate_and_send_image(message.channel, prompt)

    async def generate_and_send_image(self, channel_or_interaction, prompt, custom_params=None):
        # Determine if it's a channel or interaction
        if isinstance(channel_or_interaction, nextcord.Interaction):
            channel = channel_or_interaction.channel
            user = channel_or_interaction.user
        else:
            channel = channel_or_interaction
            user = None
            if hasattr(channel, 'guild') and channel.guild:
                user = channel.guild.get_member(channel.last_message.author.id)

        # Start with a fresh copy of the default parameters
        params = copy.deepcopy(DEFAULT_IMAGE_PARAMS)
        
        debug(f"Initial params: {json.dumps(params, indent=2)}")
        debug(f"Custom params: {json.dumps(custom_params, indent=2)}")
        
        # Generate a new random seed for each invocation
        params['params']['seed'] = str(random.randint(0, 4294967295))
        
        debug(f"Generated new seed: {params['params']['seed']}")
        
        # Update params with custom_params if provided
        if custom_params:
            params = self.deep_update(params, custom_params)
        
        debug(f"Params after update: {json.dumps(params, indent=2)}")
        
        # Add the prompt to the main body
        params['prompt'] = prompt
        
        debug(f"Final params for generation: {json.dumps(params, indent=2)}")
        
        start_time = time.time()
        
        # Create the initial embed
        embed = nextcord.Embed(title="Generating Image", description=f"Prompt: {prompt}", color=0x00ff00)
        embed.add_field(name="Status", value="Initializing...", inline=False)
        
        # Send the initial status message
        status_message = await channel.send(embed=embed)

        try:
            generate_response = await generate_image_queued(prompt, params)
            
            debug(f"Generate response: {json.dumps(generate_response, indent=2)}")
            
            if not generate_response["success"]:
                raise Exception(f"Failed to initiate image generation: {generate_response['message']}")

            job_id = generate_response["id"]
            
            embed.set_field_at(0, name="Status", value="Generation in progress...", inline=False)
            embed.add_field(name="🔢 Job ID", value=f"`{job_id}`", inline=False)
            embed.add_field(name="🖼️ Dimensions", value=f"{params['params']['width']}x{params['params']['height']}", inline=True)
            embed.add_field(name="🔄 Steps", value=f"{params['params']['steps']}", inline=True)
            embed.add_field(name="⚖️ CFG Scale", value=f"{params['params']['cfg_scale']}", inline=True)
            embed.add_field(name="🧪 Sampler", value=f"{params['params']['sampler_name']}", inline=True)
            embed.add_field(name="🎲 Seed", value=f"`{params['params']['seed']}`", inline=True)
            embed.add_field(name="🤖 Model", value=f"{params['models'][0]}", inline=True)
            
            await status_message.edit(embed=embed)
            
            check_count = 0
            progress_emojis = ["🥚", "🐣", "🐥", "🐤"]
            total_duration = 30  # 30 seconds for the emoji progression

            while time.time() - start_time < MAX_WAIT_TIME:
                check_count += 1
                elapsed_time = time.time() - start_time
                
                # Calculate progress index based on elapsed time
                progress_index = min(int((elapsed_time / total_duration) * len(progress_emojis)), len(progress_emojis) - 1)
                progress_emoji = progress_emojis[progress_index]
                
                embed.set_field_at(0, name="Status", value=f"{progress_emoji} Generation in progress...\n Check attempt: {check_count}\n⏳ Time elapsed: {elapsed_time:.1f}s", inline=False)
                await status_message.edit(embed=embed)
                
                status_response = await check_image_status_queued(job_id)
                
                if status_response["success"] and status_response["done"]:
                    # Use the chicken emoji when generation is complete
                    embed.set_field_at(0, name="Status", value="🐔 Generation complete! Preparing image...", inline=False)
                    await status_message.edit(embed=embed)
                    
                    img_url = await retrieve_generated_image_queued(job_id)
                    if img_url:
                        download_response = download_image(img_url)
                        if download_response["success"]:
                            image_path = f"generated_images/{job_id}.png"
                            with open(image_path, "wb") as f:
                                f.write(download_response["content"])
                            
                            file = nextcord.File(image_path, filename=f"{job_id}.png")
                            embed.set_image(url=f"attachment://{job_id}.png")
                            embed.set_field_at(0, name="Status", value=f"✨ Image generated in {elapsed_time:.1f}s", inline=False)
                            
                            # Create a view with the refresh, change seed, and change dimensions buttons
                            view = ImageGenerationView(self, prompt, params)
                            
                            # Mention the user who initiated the request
                            content = f"{user.mention if user else 'Your'} image is ready!"
                            
                            await status_message.delete()
                            await channel.send(content=content, embed=embed, file=file, view=view)
                            return
                
                await asyncio.sleep(CHECK_INTERVAL)
            
            # If we've reached this point, it means we've hit the timeout
            embed.color = 0xFFA500  # Orange color to indicate pending status
            embed.set_field_at(0, name="Status", value="⏳ Timeout reached. The image generation may still be in progress.", inline=False)
            
            # Add a "Check Status" button
            view = ManualCheckView(self, job_id)
            
            await status_message.edit(embed=embed, view=view)
            
            return  # Exit the function without raising an exception

        except HTTPError as http_err:
            error(f"HTTP error occurred: {http_err}")
            if http_err.response.status_code == 403:
                error_message = ("Generation failed. This might be due to high resource usage. "
                                 "Please try lowering the number of steps or reducing the image dimensions.")
            else:
                error_message = f"An error occurred while generating the image: {http_err}"
            
            embed.color = 0xff0000
            embed.set_field_at(0, name="Status", value=f"❌ Error: {error_message}", inline=False)
            
            await status_message.edit(embed=embed)

        except Exception as e:
            error(f"Error in image generation: {str(e)}")
            error_message = ("You have exceeded the compute for the generation. "
                             "Please reduce steps and/or dimensions and try again.")
            embed.color = 0xff0000
            embed.set_field_at(0, name="Status", value=f"❌ Error: {error_message}", inline=False)
            
            await status_message.edit(embed=embed)

    async def check_generation_status(self, interaction: Interaction, job_id: str):
        embed = interaction.message.embeds[0]
        
        status_response = await check_image_status_queued(job_id)
        
        if status_response["success"] and status_response["done"]:
            embed.set_field_at(0, name="Status", value="✅ Generation complete! Preparing image...", inline=False)
            await interaction.response.edit_message(embed=embed)
            
            img_url = await retrieve_generated_image_queued(job_id)
            if img_url:
                download_response = download_image(img_url)
                if download_response["success"]:
                    image_path = f"generated_images/{job_id}.png"
                    with open(image_path, "wb") as f:
                        f.write(download_response["content"])
                    
                    file = nextcord.File(image_path, filename=f"{job_id}.png")
                    embed.set_image(url=f"attachment://{job_id}.png")
                    embed.set_field_at(0, name="Status", value="✨ Image generated successfully!", inline=False)
                    
                    # Create a view with the refresh, change seed, and change dimensions buttons
                    view = ImageGenerationView(self, embed.fields[0].value.strip('`'), {})
                    
                    await interaction.edit_original_message(embed=embed, file=file, view=view)
                    return
        
        # If the image is not ready yet
        embed.set_field_at(0, name="Status", value="🔄 Image is still being generated. Please check again later.", inline=False)
        await interaction.response.edit_message(embed=embed)

    def deep_update(self, d, u):
        for k, v in u.items():
            if isinstance(v, dict):
                d[k] = self.deep_update(d.get(k, {}), v)
            else:
                d[k] = v
        return d

    async def get_available_models(self):
        try:
            result = subprocess.run(['python', 'test/workers.py'], capture_output=True, text=True, check=True)
            debug(f"Raw output from workers.py: {result.stdout}")
            
            models = set()
            current_worker_type = None
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line.startswith("Type:"):
                    current_worker_type = line.split(":")[1].strip()
                elif line.startswith("*") and current_worker_type == "image":
                    model = line[1:].strip()
                    models.add(model)
            
            available_models = list(models)
            debug(f"Available image models: {available_models}")
            return available_models
        except subprocess.CalledProcessError as e:
            error(f"Error running workers.py: {e}")
            error(f"workers.py stderr: {e.stderr}")
            raise
        except Exception as e:
            error(f"Unexpected error in get_available_models: {e}")
            raise

def setup(bot):
    bot.add_cog(ImageGeneration(bot))
    info("ImageGeneration cog setup complete")