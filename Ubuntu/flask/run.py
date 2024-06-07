# import argparse
# from app import app

# def main(use_cuda, use_gui):
#     # Configuration logic for CUDA
#     if use_cuda:
#         print("Running with GPU support.")
#     else:
#         print("Running without GPU support.")

#     # Running the Flask app with GUI mode passed as an argument
#     app.run(port=5000, debug=True, use_cuda=use_cuda, use_gui=use_gui)

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description='Run the Flask app with optional CUDA and GUI support.')
#     parser.add_argument('--cuda', action='store_true', help='Enable CUDA support for GPU processing.')
#     parser.add_argument('--gui', action='store_true', help='Enable GUI mode instead of hotkeys interaction.')
#     args = parser.parse_args()
    
#     main(args.cuda, args.gui)
