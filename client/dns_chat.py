#!/usr/bin/env python3

import dns.resolver
import dns.exception
import sys
import os
import time
import threading
from typing import Optional, List
import click
from colorama import init, Fore, Style, Back

init()

class LoadingAnimation:
    def __init__(self, message: str = "Loading"):
        self.message = message
        self.animation_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.running = False
        self.thread = None
        
    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread:
            self.thread.join()
        print(f"\r{' ' * (len(self.message) + 10)}\r", end="", flush=True)
    
    def _animate(self):
        i = 0
        while self.running:
            char = self.animation_chars[i % len(self.animation_chars)]
            print(f"\r{Fore.CYAN}{char} {self.message}{Style.RESET_ALL}", end="", flush=True)
            time.sleep(0.1)
            i += 1

class DNSChatClient:
    def __init__(self, server_host: str = "127.0.0.1", server_port: int = 53):
        self.server_host = server_host
        self.server_port = server_port
        self.api_key = ""
        
        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = [server_host]
        self.resolver.port = server_port
        self.resolver.timeout = 10
        self.resolver.lifetime = 10
    
    def set_api_key(self, api_key: str) -> bool:
        if len(api_key) != 10:
            self.print_error(f"API key must be exactly 10 characters. Got {len(api_key)} characters.")
            return False
        self.api_key = api_key
        return True
    
    def print_success(self, message: str):
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def print_error(self, message: str):
        print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")
    
    def print_info(self, message: str):
        print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")
    
    def print_warning(self, message: str):
        print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")
    
    def print_response(self, message: str):
        print(f"{Fore.CYAN}{Back.BLACK}AI Response{Style.RESET_ALL}", end="")
        print(f"{Fore.CYAN}: {message}{Style.RESET_ALL}")
        print()
    
    def query_dns(self, query: str, show_query: bool = True, loading_message: str = "Querying DNS") -> Optional[str]:
        if query == "PING":
            loading_message = "Testing connection"
        elif query == "LIST":
            loading_message = "Fetching models"
        elif len(query) > 10:
            loading_message = "Generating response"
        
        loader = LoadingAnimation(loading_message)
        
        try:
            if show_query and query in ["PING", "LIST"]:
                self.print_info(f"Querying: {query}")
            
            loader.start()
            response = self.resolver.resolve(query, 'TXT')
            loader.stop()
            
            if response:
                txt_record = str(response[0]).strip('"')
                return txt_record
            else:
                self.print_error("No response received")
                return None
                
        except dns.resolver.NXDOMAIN:
            loader.stop()
            self.print_error("Domain not found")
            return None
        except dns.resolver.NoAnswer:
            loader.stop()
            self.print_error("No TXT record found")
            return None
        except dns.resolver.Timeout:
            loader.stop()
            self.print_error("DNS query timed out")
            return None
        except dns.exception.DNSException as e:
            loader.stop()
            self.print_error(f"DNS error: {e}")
            return None
        except Exception as e:
            loader.stop()
            self.print_error(f"Unexpected error: {e}")
            return None
    
    def ping(self) -> bool:
        response = self.query_dns("PING", show_query=False)
        
        if response == "PONG":
            self.print_success("Server is responding!")
            return True
        else:
            self.print_error(f"Unexpected response: {response}")
            return False
    
    def list_models(self) -> Optional[List[str]]:
        response = self.query_dns("LIST", show_query=False)
        
        if response and response.startswith("Available models:"):
            models_str = response.replace("Available models: ", "")
            models = [model.strip() for model in models_str.split("|")]
            
            self.print_success("Available models:")
            for model in models:
                print(f"  {Fore.YELLOW}{model}{Style.RESET_ALL}")
            print()
            return models
        else:
            self.print_error(f"Unexpected response: {response}")
            return None
    
    def chat(self, model_index: int, prompt: str) -> Optional[str]:
        if not self.api_key:
            self.print_error("API key not set. Use set_api_key() first.")
            return None
        
        if not (0 <= model_index <= 9):
            self.print_error("Model index must be between 0 and 9")
            return None
        
        if not prompt.strip():
            self.print_error("Prompt cannot be empty")
            return None
        
        query = f"{self.api_key}{model_index}{prompt}"
        
        response = self.query_dns(query, show_query=False)
        
        if response:
            if response.startswith("ERROR:"):
                self.print_error(response)
                return None
            else:
                self.print_response(response)
                return response
        
        return None



@click.group()
@click.option('--host', default='127.0.0.1', help='DNS server host')
@click.option('--port', default=53, help='DNS server port')
@click.option('--api-key', help='10-character API key for authentication')
@click.pass_context
def cli(ctx, host, port, api_key):
    ctx.ensure_object(dict)
    
    client = DNSChatClient(host, port)
    
    if api_key:
        client.set_api_key(api_key)
    
    ctx.obj['client'] = client
    ctx.obj['api_key'] = api_key

@cli.command()
@click.pass_context
def ping(ctx):
    client = ctx.obj['client']
    client.ping()

@cli.command()
@click.pass_context
def list(ctx):
    client = ctx.obj['client']
    client.list_models()

@cli.command()
@click.pass_context
def interactive(ctx):
    client = ctx.obj['client']
    
    if not client.api_key:
        client.print_error("API key required for chat. Use --api-key option")
        return
    
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}🚀 DNS-based LLM Chat - Interactive Mode{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
    print()
    
    if not client.ping():
        client.print_error("Cannot connect to server. Exiting.")
        return
    
    print()
    models = client.list_models()
    if not models:
        client.print_error("Cannot fetch models. Exiting.")
        return
    
    while True:
        try:
            model_index = int(input(f"{Fore.YELLOW}Select model index (0-9): {Style.RESET_ALL}"))
            if 0 <= model_index <= 9:
                break
            else:
                client.print_error("Please enter a number between 0 and 9")
        except ValueError:
            client.print_error("Please enter a valid number")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
            return
    
    print(f"\n{Fore.GREEN}🤖 Starting chat with model {model_index}. Type 'quit' or 'exit' to leave.{Style.RESET_ALL}")
    
    while True:
        try:
            prompt = input(f"{Fore.WHITE}You: {Style.RESET_ALL}")
            
            if prompt.lower() in ['quit', 'exit', 'bye', 'q']:
                print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                break
            
            if prompt.strip():
                client.chat(model_index, prompt)
            else:
                client.print_warning("Please enter a message")
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
            break
        except EOFError:
            print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
            break

if __name__ == '__main__':
    cli()