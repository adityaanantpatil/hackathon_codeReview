"""
PDF Report Generator Module
Creates downloadable PDF reports of code reviews using FPDF2
"""

from fpdf import FPDF
from datetime import datetime


class CodeReviewPDF(FPDF):
    """Custom PDF class for code review reports"""
    
    def header(self):
        """Add header to each page"""
        # Top-right header logo
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(79, 70, 229)  # Premium Indigo
        self.cell(0, 8, 'CodeReview AI', 0, 1, 'R')
        
        # Bottom rule for header
        self.set_draw_color(229, 231, 235)  # Soft gray divider
        self.set_line_width(0.5)
        self.line(self.get_x(), self.get_y(), self.get_x() + 190, self.get_y())
        
        # Line break
        self.ln(6)
    
    def footer(self):
        """Add footer to each page"""
        self.set_y(-20)
        # Line rule for footer
        self.set_draw_color(229, 231, 235)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(156, 163, 175)  # Slate gray
        
        # Left-aligned timestamp, right-aligned page number
        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        self.cell(95, 10, f'Generated: {timestamp}', 0, 0, 'L')
        self.cell(95, 10, f'Page {self.page_no()}', 0, 1, 'R')
    

    def safe_multi_cell(self, w, h, text, border=0, align='L', fill=False):
        """Version-compatible multi_cell wrapper.

        Newer fpdf2 supports new_x/new_y. Older PyFPDF builds do not.
        This wrapper keeps the cursor at the left margin after each block
        without breaking either version.
        """
        try:
            self.multi_cell(w, h, str(text), border=border, align=align, fill=fill, new_x="LMARGIN", new_y="NEXT")
        except TypeError:
            self.multi_cell(w, h, str(text), border, align, fill)
            self.set_x(self.l_margin)

    def section_header(self, title, color=(79, 70, 229)):
        """Add a section title"""
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(*color)
        self.cell(0, 8, title.upper(), 0, 1, 'L')
        self.ln(2)
    
    def body_text(self, body):
        """Add body text. Kept compatible with older and newer FPDF versions."""
        self.set_font('Helvetica', '', 10)
        self.set_text_color(55, 65, 81)  # Slate dark gray
        self.safe_multi_cell(0, 5.5, body)
        self.ln(4)
    
    def code_block(self, code):
        """Add a code block with monospace font and a nice background."""
        self.set_font('Courier', '', 8.5)
        self.set_text_color(31, 41, 55)  # Dark slate
        self.set_fill_color(249, 250, 251)  # Off-white/light gray
        self.set_draw_color(243, 244, 246)
        
        # Output code inside a padded light gray box.
        # Avoid new_x/new_y keyword args so this works even when the user's
        # environment has an older FPDF implementation installed.
        lines = str(code).split('\n')
        code_formatted = '\n'.join(lines)
        self.safe_multi_cell(0, 4.5, code_formatted, border=1, align='L', fill=True)
        self.ln(4)
    
    def add_score_table(self, scores):
        """Add a table with scores"""
        self.set_font('Helvetica', 'B', 10)
        
        # Table header
        self.set_fill_color(79, 70, 229)  # Premium Indigo
        self.set_text_color(255, 255, 255)
        self.cell(95, 8, 'Metric', 1, 0, 'L', True)
        self.cell(95, 8, 'Score', 1, 1, 'C', True)
        
        # Table rows
        self.set_text_color(31, 41, 55)
        metrics = [
            ('Readability', scores.get('readability', 0)),
            ('Efficiency', scores.get('efficiency', 0)),
            ('Correctness', scores.get('correctness', 0)),
            ('Best Practices', scores.get('best_practices', 0))
        ]
        
        for metric, score in metrics:
            # Determine color based on score (softer tints for background)
            if score >= 8:
                self.set_fill_color(209, 250, 229)  # Soft Emerald
            elif score >= 5:
                self.set_fill_color(254, 243, 199)  # Soft Amber
            else:
                self.set_fill_color(254, 226, 226)  # Soft Rose
            
            self.set_font('Helvetica', '', 10)
            self.cell(95, 8, f'  {metric}', 1, 0, 'L', True)
            self.set_font('Helvetica', 'B', 10)
            self.cell(95, 8, f'{score}/10', 1, 1, 'C', True)
        
        self.ln(4)


def generate_pdf_report(code: str, language: str, review_data: dict) -> bytes:
    """
    Generate a PDF report from code review data.
    
    Args:
        code: Original code submitted
        language: Programming language
        review_data: Review results from Gemini
    
    Returns:
        bytes: PDF file as bytes for download
    """
    
    # Create PDF object
    pdf = CodeReviewPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()
    
    # Title Cover Area
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 22)
    pdf.set_text_color(79, 70, 229)  # Indigo
    pdf.cell(0, 10, 'Code Quality Audit Report', 0, 1, 'C')
    
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(107, 114, 128)  # Slate
    pdf.cell(0, 6, f'Language: {language}  |  Powered by Gemini AI', 0, 1, 'C')
    pdf.ln(10)
    
    # Scores Section
    pdf.section_header('Performance Scores')
    scores = review_data.get('scores', {})
    pdf.add_score_table(scores)
    
    # Overall Grade Banner
    grade = review_data.get('overall_grade', 'N/A')
    pdf.set_fill_color(243, 244, 246)
    pdf.rect(10, pdf.get_y(), 190, 15, 'F')
    
    # Text in Grade banner
    pdf.set_y(pdf.get_y() + 3.5)
    pdf.set_font('Helvetica', 'B', 12)
    pdf.set_text_color(31, 41, 55)
    pdf.cell(95, 8, '   OVERALL RATING GRADE', 0, 0, 'L')
    
    # Color based on grade
    if grade in ['A+', 'A']:
        pdf.set_text_color(16, 185, 129)  # Emerald green
    elif grade == 'B':
        pdf.set_text_color(59, 130, 246)  # Blue
    elif grade == 'C':
        pdf.set_text_color(245, 158, 11)  # Amber
    else:
        pdf.set_text_color(244, 63, 94)   # Rose/Red
        
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(85, 8, f'{grade}  ', 0, 1, 'R')
    pdf.ln(8)
    
    # Summary Section
    pdf.section_header('Executive Summary')
    summary = review_data.get('summary', 'No summary available')
    pdf.body_text(summary)
    
    # Issues Section
    pdf.section_header('Audit Details & Key Issues')
    issues = review_data.get('issues', [])
    
    if issues:
        for i, issue in enumerate(issues, 1):
            severity = issue.get('severity', 'Info')
            title = issue.get('title', 'Issue')
            lines = issue.get('lines', 'N/A')
            explanation = issue.get('explanation', 'No explanation provided')
            fix = issue.get('fix', '')
            
            # Severity color
            if severity == 'Critical':
                sev_color = (244, 63, 94)  # Rose
            elif severity == 'Warning':
                sev_color = (245, 158, 11)  # Amber
            else:
                sev_color = (59, 130, 246)  # Blue
                
            pdf.set_font('Helvetica', 'B', 10)
            pdf.set_text_color(*sev_color)
            pdf.cell(0, 6, f'{i}. [{severity}] {title} (Lines: {lines})', 0, 1)
            
            pdf.set_font('Helvetica', '', 9.5)
            pdf.set_text_color(75, 85, 99)  # Medium gray
            pdf.safe_multi_cell(0, 5, f'   {explanation}')
            
            if fix:
                pdf.set_font('Helvetica', 'I', 9.5)
                pdf.set_text_color(79, 70, 229)  # Indigo for fix
                pdf.safe_multi_cell(0, 5, f'   Fix Suggestion: {fix}')
            
            pdf.ln(3)
    else:
        pdf.body_text("No issues found! Your code is written to high standards.")
    
    # Page Break for Code Comparison
    pdf.add_page()
    
    # Original Code
    pdf.section_header('Submitted Code')
    pdf.code_block(code)
    
    # Improved Code Section
    pdf.section_header('AI Optimized & Improved Version')
    improved_code = review_data.get('improved_code', 'No improvements suggested')
    pdf.code_block(improved_code)
    
    # Learning Tips Section
    pdf.section_header('Educational Insights & Tips')
    learning_tips = review_data.get('learning_tips', [])
    
    if learning_tips:
        for i, tip in enumerate(learning_tips, 1):
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(55, 65, 81)
            pdf.safe_multi_cell(0, 5, f'{i}. {tip}')
            pdf.ln(2.5)
    else:
        pdf.body_text("Keep up the great programming practices!")
    
    # Convert PDF to bytes. This supports both fpdf2 and older PyFPDF-style output.
    output = pdf.output(dest='S')
    if isinstance(output, str):
        return output.encode('latin-1')
    return bytes(output)
