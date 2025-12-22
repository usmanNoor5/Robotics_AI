from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# UPDATE THIS WITH YOUR LOGO FILE NAME
logo_path = "NUST_logo.png"   # <-- put your image file in the same folder

pdf_path = "Assignment_2_Report.pdf"
styles = getSampleStyleSheet()

center_title = ParagraphStyle(name='CenterTitle', parent=styles['Title'], alignment=1)
center_bold = ParagraphStyle(name='CenterBold', parent=styles['Heading2'], alignment=1)
center_text = ParagraphStyle(name='CenterText', parent=styles['BodyText'], alignment=1)

doc = SimpleDocTemplate(pdf_path, pagesize=letter)
story = []

# ------------------------------------------------------
# COVER PAGE
# ------------------------------------------------------
story.append(Paragraph("Generative AI and Applications", center_title))
story.append(Spacer(1, 20))
story.append(Paragraph("Assignment #2", center_bold))
story.append(Spacer(1, 20))

# Insert logo
story.append(Image(logo_path, width=2.5*inch, height=2.5*inch))
story.append(Spacer(1, 20))

story.append(Paragraph("<b>SUBMITTED TO:</b>", center_bold))
story.append(Paragraph("Dr. Yasar Ayaz", center_text))
story.append(Spacer(1, 20))

story.append(Paragraph("<b>SUBMITTED BY (Group #4):</b>", center_bold))
story.append(Paragraph("Muhammad Usman Noor    Reg: 539240", center_text))
story.append(Spacer(1, 40))

story.append(Paragraph("School of Mechanical & Manufacturing Engineering", center_text))
story.append(Paragraph("National University of Sciences & Technology", center_text))
story.append(PageBreak())

# ------------------------------------------------------
# CONTENT PAGE
# ------------------------------------------------------
content = """
<b>Comparison of RNN and LSTM for Stock Prediction</b><br/><br/>

<b>Difference Between RNN and LSTM</b><br/>
• RNN cannot store long-term memory due to vanishing gradients.<br/>
• LSTM uses gates (forget, input, output) to store long-term patterns.<br/>
• This makes LSTM more powerful for time-series forecasting.<br/><br/>

<b>Prediction Behavior</b><br/>
• RNN predictions fluctuate and lag behind actual prices.<br/>
• LSTM predictions are smoother and follow the real trend closely.<br/><br/>

<b>Learning Curve Differences</b><br/>
• RNN validation loss plateaus early.<br/>
• LSTM decreases steadily and generalizes better.<br/><br/>

<b>Loss Comparison</b><br/>
• RNN has higher MAE/RMSE.<br/>
• LSTM performs significantly better for long sequences.<br/><br/>

LSTM clearly outperforms RNN in stock price forecasting due to its ability
to remember long-term dependencies effectively.
"""

story.append(Paragraph(content, styles['BodyText']))

doc.build(story)

print("Report created:", pdf_path)
