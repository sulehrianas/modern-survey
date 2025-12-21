"""
Service to generate PDF reports using the reportlab library.
"""
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_traverse_report(title_text, summary_data, traverse_df, file_path):
    """
    Generates a PDF report for a compass traverse calculation.

    Args:
        title_text (str): The main title of the report.
        summary_data (dict): A dictionary containing key-value pairs for the summary section.
        traverse_df (pd.DataFrame): A DataFrame with the main traverse data.
        file_path (str): The path to save the generated PDF file.

    Returns:
        bool: True if the report was generated successfully, False otherwise.
    """
    try:
        doc = SimpleDocTemplate(file_path,
                                rightMargin=inch/2, leftMargin=inch/2,
                                topMargin=inch/2, bottomMargin=inch/2)
        
        story = []
        styles = getSampleStyleSheet()

        # 1. Title
        story.append(Paragraph(title_text, styles['h1']))
        story.append(Spacer(1, 0.2*inch))

        # 2. Calculation Summary
        story.append(Paragraph("Calculation Summary", styles['h2']))
        summary_list = [[key, value] for key, value in summary_data.items()]
        summary_table = Table(summary_list, colWidths=[2.5*inch, 4.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))

        # 3. Traverse Data Table
        story.append(Paragraph("Adjusted Traverse Data", styles['h2']))
        
        # Convert dataframe to list of lists for the table, including headers
        data_list = [traverse_df.columns.values.tolist()] + traverse_df.values.tolist()
        
        data_table = Table(data_list, repeatRows=1) # Repeat header on new pages
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        story.append(data_table)

        # *** This is the crucial step that was missing ***
        # Build the document
        doc.build(story)

        return True

    except Exception as e:
        # In a real application, you'd want to log this error
        print(f"Error generating PDF: {e}")
        return False

def generate_leveling_report(summary_data, leveling_df, file_path):
    """
    Generates a PDF report for a differential leveling calculation.

    Args:
        summary_data (dict): A dictionary containing key-value pairs for the summary.
        leveling_df (pd.DataFrame): A DataFrame with the main leveling data.
        file_path (str): The path to save the generated PDF file.

    Returns:
        bool: True if the report was generated successfully, False otherwise.
    """
    try:
        doc = SimpleDocTemplate(file_path,
                                rightMargin=inch/2, leftMargin=inch/2,
                                topMargin=inch/2, bottomMargin=inch/2)
        
        story = []
        styles = getSampleStyleSheet()

        # 1. Title
        story.append(Paragraph("Differential Leveling Report", styles['h1']))
        story.append(Spacer(1, 0.2*inch))

        # 2. Calculation Summary
        story.append(Paragraph("Calculation Summary", styles['h2']))
        summary_list = [[key, value] for key, value in summary_data.items()]
        summary_table = Table(summary_list, colWidths=[2.5*inch, 4.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))

        # 3. Leveling Data Table
        story.append(Paragraph("Leveling Field Notes", styles['h2']))
        data_list = [leveling_df.columns.values.tolist()] + leveling_df.values.tolist()
        data_table = Table(data_list, repeatRows=1)
        # Apply similar styling as the traverse report table
        data_table.setStyle(TableStyle(generate_traverse_report.__defaults__[0][10].getCommands()))
        story.append(data_table)

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error generating leveling PDF: {e}")
        return False

def generate_trig_leveling_report(summary_data, observations_df, file_path):
    """
    Generates a PDF report for a trigonometric leveling calculation.

    Args:
        summary_data (dict): A dictionary containing key-value pairs for the station setup.
        observations_df (pd.DataFrame): A DataFrame with the main observation data.
        file_path (str): The path to save the generated PDF file.

    Returns:
        bool: True if the report was generated successfully, False otherwise.
    """
    try:
        doc = SimpleDocTemplate(file_path,
                                rightMargin=inch/2, leftMargin=inch/2,
                                topMargin=inch/2, bottomMargin=inch/2)
        
        story = []
        styles = getSampleStyleSheet()

        # 1. Title
        story.append(Paragraph("Trigonometric Leveling Report", styles['h1']))
        story.append(Spacer(1, 0.2*inch))

        # 2. Station Setup Summary
        story.append(Paragraph("Instrument Station Setup", styles['h2']))
        summary_list = [[key, value] for key, value in summary_data.items()]
        summary_table = Table(summary_list, colWidths=[2.5*inch, 4.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))

        # 3. Observations Data Table
        story.append(Paragraph("Observations and Results", styles['h2']))
        data_list = [observations_df.columns.values.tolist()] + observations_df.values.tolist()
        data_table = Table(data_list, repeatRows=1)
        data_table.setStyle(TableStyle(generate_traverse_report.__defaults__[0][10].getCommands()))
        story.append(data_table)

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error generating Trig. Leveling PDF: {e}")
        return False

def generate_theodolite_report(summary_data, traverse_df, file_path):
    """
    Generates a PDF report for a theodolite traverse calculation.

    Args:
        summary_data (dict): A dictionary containing key-value pairs for the summary section.
        traverse_df (pd.DataFrame): A DataFrame with the main traverse data.
        file_path (str): The path to save the generated PDF file.

    Returns:
        bool: True if the report was generated successfully, False otherwise.
    """
    try:
        doc = SimpleDocTemplate(file_path,
                                rightMargin=inch/2, leftMargin=inch/2,
                                topMargin=inch/2, bottomMargin=inch/2)
        
        story = []
        styles = getSampleStyleSheet()

        # 1. Title
        story.append(Paragraph("Theodolite Traverse Report", styles['h1']))
        story.append(Spacer(1, 0.2*inch))

        # 2. Calculation Summary
        story.append(Paragraph("Calculation Summary", styles['h2']))
        summary_list = [[key, value] for key, value in summary_data.items()]
        summary_table = Table(summary_list, colWidths=[2.5*inch, 4.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.2*inch))

        # 3. Traverse Data Table
        story.append(Paragraph("Traverse Field Data & Results", styles['h2']))
        data_list = [traverse_df.columns.values.tolist()] + traverse_df.values.tolist()
        data_table = Table(data_list, repeatRows=1)
        data_table.setStyle(TableStyle(generate_traverse_report.__defaults__[0][10].getCommands()))
        story.append(data_table)

        doc.build(story)
        return True
    except Exception as e:
        print(f"Error generating Theodolite PDF: {e}")
        return False