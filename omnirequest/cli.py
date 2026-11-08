from omnirequest.app import app
import argparse

def main():
    parser = argparse.ArgumentParser(description="OmniRequest - HTTP Request Converter")
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="IP address to bind the server to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=5001, 
        help="Port number to run the server on (default: 5001)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable Flask debug mode"
    )
    
    args = parser.parse_args()

    print("\n========================================")
    print("          OMNIREQUEST v1.0")
    print("========================================")
    print("[+] JS, Python, PHP, Go, C#, Java, Ruby, Rust")
    print("[+] Automatic Cookie & Credential Detection")
    print("========================================")
    print(f"[*] Running on http://{args.host}:{args.port} (Debug: {args.debug})")
    print("========================================\n")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == "__main__":
    main()