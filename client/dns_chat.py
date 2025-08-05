#!/usr/bin/env python3

import dns.resolver
import dns.exception
import sys
import os
from typing import Optional, List
import click
from colorama import init, Fore, Style, Back

init()

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
        print(f"{Fore.CYAN}{Back.BLACK} AI Response {Style.RESET_ALL}")
        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")
        print()
    
    def query_dns(self, query: str, show_query: bool = True) -> Optional[str]:
        try:
            if show_query and query in ["PING", "LIST"]:
                self.print_info(f"Querying: {query}")
            
            response = self.resolver.resolve(query, 'TXT')
            
            if response:
                txt_record = str(response[0]).strip('"')
                return txt_record
            else:
                self.print_error("No response received")
                return None
                
        except dns.resolver.NXDOMAIN:
            self.print_error("Domain not found")
            return None
        except dns.resolver.NoAnswer:
            self.print_error("No TXT record found")
            return None
        except dns.resolver.Timeout:
            self.print_error("DNS query timed out")
            return None
        except dns.exception.DNSException as e:
            self.print_error(f"DNS error: {e}")
            return None
        except Exception as e:
            self.print_error(f"Unexpected error: {e}")
            return None
    
    def ping(self) -> bool:
        self.print_info("Testing server connectivity...")
        response = self.query_dns("PING", show_query=True)
        
        if response == "PONG":
            self.print_success("Server is responding!")
            return True
        else:
            self.print_error(f"Unexpected response: {response}")
            return False
    
    def list_models(self) -> Optional[List[str]]:
        self.print_info("Fetching available models...")
        response = self.query_dns("LIST", show_query=True)
        
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
        
        self.print_info(f"Model {model_index}: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
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