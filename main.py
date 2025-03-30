from ui import create_ui

if __name__ == "__main__":
    demo = create_ui()
    # Launch the Gradio app with a public link
    demo.launch(share=True)
