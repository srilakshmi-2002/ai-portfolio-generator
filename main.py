import streamlit as st
import os
import zipfile
import PyPDF2
from io import BytesIO
from docx import Document
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit.components.v1 as components

# 1. Page Config (Must be first)
st.set_page_config(page_title="AI Portfolio Generator", page_icon="📜", layout="wide")

# 2. Load Environment Variables
load_dotenv()

# 3. Check API Key
api_key = os.getenv("gemini")
if not api_key:
    st.error("⚠️ Google API Key missing! Please check your .env file.")
    st.stop()

os.environ["GOOGLE_API_KEY"] = api_key

st.title("🚀 AI-Generated Portfolio from Resume")
st.markdown("Upload your resume, and this AI will build a website for you in seconds.")

# Session State for storing data
if "generated_zip" not in st.session_state:
    st.session_state["generated_zip"] = None
if "website_html" not in st.session_state:
    st.session_state["website_html"] = None

# File Upload
upload_file = st.file_uploader("Upload Resume (PDF or Word)", type=["pdf", "docx"])

def extract_text(file):
    """Extract text from uploaded file"""
    text = ""
    try:
        if file.name.endswith(".pdf"):
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        elif file.name.endswith(".docx"):
            doc = Document(file)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return None
    return text

# Generate Button
if st.button("✨ Generate Portfolio Website"):
    if upload_file is not None:
        with st.spinner("🤖 AI is analyzing your resume and coding the website..."):
            
            # Step 1: Get Text
            resume_content = extract_text(upload_file)
            
            if resume_content:
                # Step 2: Call Gemini AI
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
                
                prompt = f"""
                You are a professional web developer. Create a personal portfolio website based on this resume:
                {resume_content}

                RULES:
                1. Make it modern, responsive, and colorful.
                2. Include sections: Home, About, Skills, Projects, Contact.
                3. IMPORTANT: In the Contact section, DO NOT include a functional form (no <form> tags). ONLY display the Email and Phone number clearly.
                4. OUTPUT FORMAT MUST BE EXACTLY LIKE THIS (Do not add markdown ``` blocks):

                --html--
                <!DOCTYPE html>
                <html>...code...</html>
                --html--

                --css--
                body {{ ...code... }}
                --css--

                --js--
                console.log('...');
                --js--
                """
                
                try:
                    response = llm.invoke(prompt)
                    content = response.content

                    # Step 3: Parse Output
                    # Robust parsing to handle potential AI formatting variations
                    try:
                        html_code = content.split("--html--")[1].strip()
                        css_code = content.split("--css--")[1].strip()
                        js_code = content.split("--js--")[1].strip()
                        
                        # Step 4: Create ZIP in Memory
                        zip_buffer = BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w") as zf:
                            zf.writestr("index.html", html_code)
                            zf.writestr("style.css", css_code)
                            zf.writestr("script.js", js_code)
                        
                        # Save to Session State
                        st.session_state["generated_zip"] = zip_buffer.getvalue()
                        
                        # Create a full HTML string for preview (injecting CSS/JS)
                        full_preview = f"""
                        <html>
                        <head><style>{css_code}</style></head>
                        <body>
                        {html_code}
                        <script>{js_code}</script>
                        </body>
                        </html>
                        """
                        st.session_state["website_html"] = full_preview
                        
                        st.success("✅ Website Generated Successfully!")
                        
                    except IndexError:
                        st.error("⚠️ AI Parsing Error: The model didn't format the code correctly. Please try again.")
                
                except Exception as e:
                    st.error(f"An error occurred: {e}")
    else:
        st.warning("⚠️ Please upload a resume first.")

# Display Result
if st.session_state["website_html"]:
    st.divider()
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🖥️ Live Preview")
        components.html(st.session_state["website_html"], height=500, scrolling=True)
    
    with col2:
        st.subheader("⬇️ Download Code")
        st.write("Get the full source code files (HTML, CSS, JS).")
        st.download_button(
            label="Download Website (.zip)",
            data=st.session_state["generated_zip"],
            file_name="my_portfolio.zip",
            mime="application/zip"
        )