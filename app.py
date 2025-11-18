import gradio as gr

def greet(name, intensity):
    return "Hello, " + name + "!" * int(intensity)

demo = gr.Interface(
    fn=greet,
    inputs=[
        "text",
        "slider"
    ],
    outputs=["text"],
    title="Greeting App",
    description="Enter your name and select the intensity of the greeting."
)

demo.launch()
