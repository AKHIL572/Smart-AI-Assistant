import streamlit as st
import google.generativeai as genai
import os
import base64
import re
import json
import time
import io
from dotenv import load_dotenv
from PIL import Image
from PyPDF2 import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from datetime import datetime

# ============================================
# CONFIGURATION & SETUP
# ============================================

load_dotenv()

# Validate environment variables
REQUIRED_ENV = ['GOOGLE_API_KEY']
missing = [var for var in REQUIRED_ENV if not os.getenv(var)]
if missing:
    st.error(f"Missing environment variables: {', '.join(missing)}")
    st.stop()

# Initialize model with error handling
try:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    # Test model connectivity
    model.generate_content("test")
except Exception as e:
    st.error(f"Failed to initialize AI model: {e}")
    st.stop()

# ============================================
# UI CONFIGURATION
# ============================================

st.set_page_config(page_title="Smart AI Assistant",
                   page_icon="🤖", layout="wide")


def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()


# CSS Styling
try:
    logo_base64 = get_base64_of_bin_file("project_logo.png")
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="custom-logo">'
except:
    logo_html = '<span style="font-size:30px;">🚀</span>'

st.markdown(f"""
    <style>
    .block-container {{ padding-top: 2rem; }}
    [data-testid="stSidebarHeader"] {{ display: none !important; }}
    [data-testid="stSidebarContent"] {{ padding-top: 1rem !important; }}
    .logo-container {{
        display: flex;
        align-items: center;
        gap: 12px;
        margin-left: 5px;
        margin-bottom: 20px;
    }}
    .custom-logo {{ width: 40px; height: auto; pointer-events: none; }}
    .sidebar-title {{ color: #40E0D0; font-size: 20px; font-weight: 600; margin: 0; }}
    .download-section {{
        background-color: #1a1a1a;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }}
    </style>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR
# ============================================

with st.sidebar:
    st.markdown(f"""
        <div class="logo-container">
            {logo_html}
            <p class="sidebar-title">AI Suite</p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    option = st.selectbox(
        "Select a Feature",
        ["Chat with AI", "Food Image Analyzer",
            "YouTube Summarizer", "PDF Document Chat"],
        help="Choose an AI-powered tool to assist you"
    )


# ============================================
# HELPER FUNCTIONS
# ============================================


def safe_generate_content(prompt, max_retries=2):
    """Wrapper for model generation with retry logic and error handling"""
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            if response.text:
                return response.text, None
            return None, "Empty response from model"
        except Exception as e:
            if attempt == max_retries - 1:
                return None, f"AI Error: {str(e)}"
            time.sleep(1)
    return None, "Max retries exceeded"


def extract_transcript_details(youtube_video_url):
    """Extract YouTube transcript with specific error handling"""
    try:
        # Extract Video ID using regex patterns
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
            r'(?:shorts\/)([0-9A-Za-z_-]{11})'
        ]
        video_id = None
        for pattern in patterns:
            match = re.search(pattern, youtube_video_url)
            if match:
                video_id = match.group(1)
                break

        if not video_id:
            return None, "Invalid YouTube URL format"

        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        transcript_text = " ".join([snippet.text for snippet in transcript])
        return transcript_text, None

    except TranscriptsDisabled:
        return None, "Transcripts are disabled for this video"
    except NoTranscriptFound:
        return None, "No transcript found. Video may not have captions."
    except VideoUnavailable:
        return None, "Video is unavailable (private, deleted, or age-restricted)"
    except Exception as e:
        return None, f"Unexpected error: {str(e)}"


def extract_pdf_text(pdf_file, max_pages=50, max_chars=15000):
    """Extract PDF text with memory protection"""
    try:
        reader = PdfReader(pdf_file)
        text_parts = []
        total_chars = 0
        total_pages = len(reader.pages)

        for i, page in enumerate(reader.pages[:max_pages]):
            page_text = page.extract_text()
            if page_text:
                if total_chars + len(page_text) > max_chars:
                    remaining = max_chars - total_chars
                    text_parts.append(page_text[:remaining])
                    st.warning(
                        f"PDF truncated: processed {i+1} of {total_pages} pages (character limit reached)")
                    break
                text_parts.append(page_text)
                total_chars += len(page_text)

        full_text = " ".join(text_parts)
        return full_text, None

    except Exception as e:
        return None, f"PDF Error: {e}"


def create_nutrition_pdf(data, img_file, detailed_text=None):
    """Create a professional PDF nutrition report"""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Nutrition Analysis Report", ln=True, align="C")
    pdf.ln(10)

    # Date
    pdf.set_font("Arial", "", 12)
    pdf.cell(
        0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(10)

    # Food Image
    if img_file:
        img_path = "temp_food.jpg"
        img_file.save(img_path)
        pdf.image(img_path, x=60, w=90)
        pdf.ln(10)

    # Detailed Analysis Section
    if detailed_text:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Detailed Analysis", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", "", 11)
        # Clean markdown for PDF
        clean_text = detailed_text.replace('**', '').replace('#', '')
        pdf.multi_cell(0, 6, clean_text)
        pdf.ln(10)

    # Summary Table
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Nutritional Summary", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "", 12)
    nutrition_data = [
        ["Food Name", str(data.get('food_name', 'Unknown'))],
        ["Calories", str(data.get('calories', 'N/A'))],
        ["Protein", str(data.get('protein', 'N/A'))],
        ["Carbohydrates", str(data.get('carbs', 'N/A'))],
        ["Fats", str(data.get('fats', 'N/A'))],
        ["Health Rating", f"{data.get('health_rating', 'N/A')}/10"]
    ]

    for item, value in nutrition_data:
        pdf.cell(60, 10, f"{item}:", border=1)
        pdf.cell(0, 10, value, border=1, ln=True)

    pdf.ln(10)

    # Footer
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Generated by Smart AI Assistant", ln=True, align="C")

    return pdf.output(dest="S").encode("latin-1")


def create_nutrition_excel(data, detailed_text=None):
    """Create Excel file with nutrition data"""
    import pandas as pd

    # Create summary DataFrame
    summary_df = pd.DataFrame([{
        'Food Name': data.get('food_name', 'Unknown'),
        'Calories': data.get('calories', 'N/A'),
        'Protein (g)': data.get('protein', 'N/A'),
        'Carbs (g)': data.get('carbs', 'N/A'),
        'Fats (g)': data.get('fats', 'N/A'),
        'Health Rating': f"{data.get('health_rating', 'N/A')}/10",
        'Notes': data.get('notes', ''),
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }])

    # Create detailed analysis DataFrame
    if detailed_text:
        detailed_df = pd.DataFrame([{
            'Detailed Analysis': detailed_text,
            'Date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }])
    else:
        detailed_df = pd.DataFrame()

    # Create Excel in memory with multiple sheets
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        summary_df.to_excel(writer, index=False, sheet_name='Summary')
        if not detailed_df.empty:
            detailed_df.to_excel(writer, index=False,
                                 sheet_name='Detailed Analysis')

        # Auto-adjust column widths for summary sheet
        worksheet = writer.sheets['Summary']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)
    return output.getvalue()


def create_nutrition_csv(data, detailed_text=None):
    """Create CSV file with nutrition data"""
    import pandas as pd

    nutrition_df = pd.DataFrame([{
        'Food Name': data.get('food_name', 'Unknown'),
        'Calories': data.get('calories', 'N/A'),
        'Protein (g)': data.get('protein', 'N/A'),
        'Carbs (g)': data.get('carbs', 'N/A'),
        'Fats (g)': data.get('fats', 'N/A'),
        'Health Rating': f"{data.get('health_rating', 'N/A')}/10",
        'Notes': data.get('notes', ''),
        'Detailed Analysis': detailed_text if detailed_text else '',
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }])

    return nutrition_df.to_csv(index=False)


# ============================================
# PDF & EXCEL GENERATION FUNCTIONS
# ============================================

def create_nutrition_pdf(data, img_file):
    """Create a professional PDF nutrition report"""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 10, "Nutrition Analysis Report", ln=True, align="C")
    pdf.ln(10)

    # Date
    pdf.set_font("Arial", "", 12)
    pdf.cell(
        0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
    pdf.ln(10)

    # Food Image
    if img_file:
        img_path = "temp_food.jpg"
        img_file.save(img_path)
        pdf.image(img_path, x=60, w=90)
        pdf.ln(10)

    # Food Name
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Food: {data.get('food_name', 'Unknown')}", ln=True)
    pdf.ln(5)

    # Nutrition Table
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Nutritional Information:", ln=True)

    pdf.set_font("Arial", "", 12)
    nutrition_data = [
        ["Calories", str(data.get('calories', 'N/A'))],
        ["Protein", str(data.get('protein', 'N/A'))],
        ["Carbohydrates", str(data.get('carbs', 'N/A'))],
        ["Fats", str(data.get('fats', 'N/A'))],
        ["Health Rating", f"{data.get('health_rating', 'N/A')}/10"]
    ]

    for item, value in nutrition_data:
        pdf.cell(60, 10, f"{item}:", border=1)
        pdf.cell(0, 10, value, border=1, ln=True)

    pdf.ln(10)

    # Notes
    if data.get('notes'):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Additional Notes:", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, data['notes'])

    # Footer
    pdf.ln(20)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Generated by Smart AI Assistant", ln=True, align="C")

    return pdf.output(dest="S").encode("latin-1")


def create_nutrition_excel(data):
    """Create Excel file with nutrition data"""
    import pandas as pd

    # Create DataFrame
    nutrition_df = pd.DataFrame([{
        'Food Name': data.get('food_name', 'Unknown'),
        'Calories': data.get('calories', 'N/A'),
        'Protein (g)': data.get('protein', 'N/A'),
        'Carbs (g)': data.get('carbs', 'N/A'),
        'Fats (g)': data.get('fats', 'N/A'),
        'Health Rating': f"{data.get('health_rating', 'N/A')}/10",
        'Notes': data.get('notes', ''),
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }])

    # Create Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        nutrition_df.to_excel(writer, index=False, sheet_name='Nutrition Data')

        # Auto-adjust column widths
        worksheet = writer.sheets['Nutrition Data']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)
    return output.getvalue()


def create_nutrition_csv(data):
    """Create CSV file with nutrition data"""
    import pandas as pd

    nutrition_df = pd.DataFrame([{
        'Food Name': data.get('food_name', 'Unknown'),
        'Calories': data.get('calories', 'N/A'),
        'Protein (g)': data.get('protein', 'N/A'),
        'Carbs (g)': data.get('carbs', 'N/A'),
        'Fats (g)': data.get('fats', 'N/A'),
        'Health Rating': f"{data.get('health_rating', 'N/A')}/10",
        'Notes': data.get('notes', ''),
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M')
    }])

    return nutrition_df.to_csv(index=False)


# ============================================
# MAIN CONTENT
# ============================================

st.header("🤖 Smart AI Assistant")

# --------------------------------------------
# FEATURE: Chat with AI
# --------------------------------------------
if option == "Chat with AI":
    st.subheader("General Assistant")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Ask me anything:"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            # Build conversation history for context
            try:
                chat = model.start_chat(history=[
                    {"role": m["role"], "parts": [m["content"]]}
                    for m in st.session_state.messages[:-1]
                ])
                response = chat.send_message(prompt)

                if response.text:
                    st.session_state.messages.append(
                        {"role": "model", "content": response.text})
                else:
                    st.session_state.messages.append(
                        {"role": "model", "content": "Sorry, I couldn't generate a response."})
            except Exception as e:
                st.error(f"Chat error: {e}")

        # Rerun to display new messages
        st.rerun()

# --------------------------------------------
# FEATURE: Food Image Analyzer
# --------------------------------------------

elif option == "Food Image Analyzer":
    st.subheader("🍎 Nutrition Expert")

    uploaded_file = st.file_uploader(
        "Upload food photo...", type=["jpg", "png", "jpeg"])

    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=400)

        if st.button("Analyze Nutrition"):
            with st.spinner("Analyzing..."):
                # First, get detailed analysis (visible on screen)
                detailed_prompt = """Analyze this food image in detail. Identify each food item visible, estimate portion sizes, 
                and provide nutritional information for each item separately. Then provide a total summary.
                
                Format your response as:
                
                **Identified Food Items:**
                1. [Food name] - [portion size]
                   - Calories: X
                   - Protein: Xg
                   - Carbs: Xg
                   - Fats: Xg
                
                2. [Next item...]
                
                **Total Nutritional Values:**
                - Total Calories: X
                - Total Protein: Xg
                - Total Carbs: Xg
                - Total Fats: Xg
                
                **Health Assessment:**
                [Brief health notes and recommendations]"""

                # Second, get structured data for downloads (hidden processing)
                structured_prompt = """Analyze this food image and provide ONLY the following information in JSON format:
                {
                    "food_name": "name of the food",
                    "calories": "estimated calories with unit",
                    "protein": "estimated protein in grams",
                    "carbs": "estimated carbs in grams",
                    "fats": "estimated fats in grams",
                    "health_rating": number from 1-10,
                    "notes": "brief health notes"
                }
                Return ONLY valid JSON, no markdown formatting."""

                try:
                    # Get detailed visible analysis
                    detailed_response = model.generate_content(
                        [detailed_prompt, img])
                    detailed_text = detailed_response.text

                    # Display detailed analysis on screen
                    st.markdown("### 📋 Detailed Analysis")
                    st.markdown(detailed_text)

                    st.divider()

                    # Get structured data for metrics and downloads
                    structured_response = model.generate_content(
                        [structured_prompt, img])
                    response_text = structured_response.text.replace(
                        '```json', '').replace('```', '').strip()

                    # Parse JSON
                    data = json.loads(response_text)

                    # Display structured totals
                    st.markdown("### 📊 Nutritional Summary")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Calories", data.get('calories', 'N/A'))
                    col2.metric("Protein", data.get('protein', 'N/A'))
                    col3.metric("Health Score",
                                f"{data.get('health_rating', 'N/A')}/10")

                    st.subheader(f"🍽️ {data.get('food_name', 'Unknown Food')}")

                    col4, col5 = st.columns(2)
                    col4.metric("Carbs", data.get('carbs', 'N/A'))
                    col5.metric("Fats", data.get('fats', 'N/A'))

                    if data.get('notes'):
                        st.info(f"**Notes:** {data['notes']}")

                    # ============================================
                    # DOWNLOAD SECTION
                    # ============================================
                    st.divider()
                    st.subheader("📥 Download Report")

                    # Create download buttons in columns
                    col_pdf, col_excel, col_csv = st.columns(3)

                    with col_pdf:
                        pdf_bytes = create_nutrition_pdf(
                            data, img, detailed_text)
                        st.download_button(
                            label="📄 PDF Report",
                            data=pdf_bytes,
                            file_name=f"nutrition_report_{data.get('food_name', 'food').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

                    with col_excel:
                        excel_bytes = create_nutrition_excel(
                            data, detailed_text)
                        st.download_button(
                            label="📊 Excel Sheet",
                            data=excel_bytes,
                            file_name=f"nutrition_data_{data.get('food_name', 'food').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )

                    with col_csv:
                        csv_data = create_nutrition_csv(data, detailed_text)
                        st.download_button(
                            label="📋 CSV File",
                            data=csv_data,
                            file_name=f"nutrition_data_{data.get('food_name', 'food').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                except json.JSONDecodeError:
                    st.warning(
                        "Couldn't parse structured data. Showing raw response:")
                    st.write(detailed_response.text)
                except Exception as e:
                    st.error(f"Analysis error: {e}")

# --------------------------------------------
# FEATURE: YouTube Summarizer
# --------------------------------------------
elif option == "YouTube Summarizer":
    st.subheader("🎥 Video Content Analyst")

    youtube_link = st.text_input("Enter YouTube Video Link:")

    if youtube_link:
        try:
            v_id = youtube_link.split("v=")[1].split(
                "&")[0] if "v=" in youtube_link else youtube_link.split("/")[-1]
            st.image(f"http://img.youtube.com/vi/{v_id}/0.jpg", width=350)
        except:
            pass

        if st.button("Get Detailed Summary"):
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Extracting transcript...")
            progress_bar.progress(30)

            transcript, error = extract_transcript_details(youtube_link)

            if error:
                progress_bar.empty()
                status_text.empty()
                st.error(error)
            else:
                status_text.text("Generating summary...")
                progress_bar.progress(70)

                try:
                    summary_prompt = f"Provide a comprehensive summary of this YouTube video transcript. Include key points, main topics, and important takeaways:\n\n{transcript[:10000]}"
                    summary, error = safe_generate_content(summary_prompt)

                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()

                    if error:
                        st.error(error)
                    else:
                        st.success("Summary generated!")
                        st.write(summary)

                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Summarization error: {e}")

# --------------------------------------------
# FEATURE: PDF Document Chat
# --------------------------------------------
elif option == "PDF Document Chat":
    st.subheader("📄 Intelligent Document Analyst")

    pdf_file = st.file_uploader("Upload PDF file", type=["pdf"])

    if pdf_file:
        user_q = st.text_input("Question about document:")

        if st.button("Search Document") and user_q:
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Processing PDF...")
            progress_bar.progress(30)

            text, error = extract_pdf_text(pdf_file)

            if error:
                progress_bar.empty()
                status_text.empty()
                st.error(error)
            else:
                status_text.text("Analyzing content...")
                progress_bar.progress(60)

                try:
                    prompt = f"""Based on the following PDF content, please answer the question. 
                    If the answer is not in the document, say so clearly.
                    
                    PDF Content:
                    {text[:12000]}
                    
                    Question: {user_q}
                    
                    Answer:"""

                    answer, error = safe_generate_content(prompt)

                    progress_bar.progress(100)
                    status_text.empty()
                    progress_bar.empty()

                    if error:
                        st.error(error)
                    else:
                        st.success("Answer found!")
                        st.write(answer)

                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Analysis error: {e}")
