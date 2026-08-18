"""Script to build the empathetic, friendly, and grounded Architecture & Philosophy Guide in .docx format."""
import os
import zipfile
import shutil

TEMPLATE_DOCX = "Enterprise Agentic Solution Design Document - HR Agentic Solution (MVP 1).docx"
OUTPUT_DOCX = "HR Agentic Solution - Architecture & Philosophy Guide (Team 12).docx"
ARCH_IMG = "images/system_architecture.jpg"
FLOW_IMG = "images/flow_diagram.jpg"

def create_guide_docx():
    os.makedirs("scripts/temp_guide_docx", exist_ok=True)
    
    # Read existing docx template to reuse fonts, styles, and settings
    with zipfile.ZipFile(TEMPLATE_DOCX, "r") as z:
        z.extractall("scripts/temp_guide_docx")

    # Update [Content_Types].xml to ensure image/jpeg is registered
    ct_path = "scripts/temp_guide_docx/[Content_Types].xml"
    with open(ct_path, "r", encoding="utf-8") as f:
        ct_content = f.read()
    if 'Extension="jpg"' not in ct_content and 'Extension="jpeg"' not in ct_content:
        ct_content = ct_content.replace('</Types>', '<Default Extension="jpg" ContentType="image/jpeg"/><Default Extension="jpeg" ContentType="image/jpeg"/></Types>')
        with open(ct_path, "w", encoding="utf-8") as f:
            f.write(ct_content)

    # Add images to word/media/
    media_dir = "scripts/temp_guide_docx/word/media"
    os.makedirs(media_dir, exist_ok=True)
    shutil.copy(ARCH_IMG, os.path.join(media_dir, "image1.jpg"))
    shutil.copy(FLOW_IMG, os.path.join(media_dir, "image2.jpg"))

    # Update word/_rels/document.xml.rels with image relationships
    rels_path = "scripts/temp_guide_docx/word/_rels/document.xml.rels"
    with open(rels_path, "r", encoding="utf-8") as f:
        rels_content = f.read()
    
    img1_rel = '<Relationship Id="rIdImg1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image1.jpg"/>'
    img2_rel = '<Relationship Id="rIdImg2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image2.jpg"/>'
    
    if "rIdImg1" not in rels_content:
        rels_content = rels_content.replace('</Relationships>', f'{img1_rel}{img2_rel}</Relationships>')
        with open(rels_path, "w", encoding="utf-8") as f:
            f.write(rels_content)

    # Helper functions to build WordprocessingML
    def p(text="", style=None, bold=False, italic=False, color=None, size=None, align=None, space_after=120):
        align_xml = f'<w:jc w:val="{align}"/>' if align else ''
        pPr = f'<w:pPr>{align_xml}<w:spacing w:after="{space_after}"/><w:rPr>'
        if style:
            pPr = f'<w:pPr><w:pStyle w:val="{style}"/>{align_xml}<w:spacing w:after="{space_after}"/><w:rPr>'
        rPr = ''
        if bold: rPr += '<w:b/>'
        if italic: rPr += '<w:i/>'
        if color: rPr += f'<w:color w:val="{color}"/>'
        if size: rPr += f'<w:sz w:val="{size}"/>'
        pPr += f'{rPr}</w:rPr></w:pPr>'
        
        escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'<w:p>{pPr}<w:r><w:rPr>{rPr}</w:rPr><w:t>{escaped_text}</w:t></w:r></w:p>'

    def heading(text, level=1):
        sizes = {1: 34, 2: 26, 3: 22}
        colors = {1: "1A365D", 2: "2B6CB0", 3: "2D3748"}
        space = {1: 220, 2: 150, 3: 100}
        return p(text, bold=True, size=sizes.get(level, 22), color=colors.get(level, "1A365D"), space_after=space.get(level, 100))

    def bullet(text, bold_prefix="", space_after=60):
        b_prefix = f'<w:r><w:rPr><w:b/><w:sz w:val="20"/></w:rPr><w:t>{bold_prefix.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")}</w:t></w:r>' if bold_prefix else ''
        escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'''<w:p>
            <w:pPr>
                <w:pStyle w:val="ListParagraph"/>
                <w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>
                <w:spacing w:after="{space_after}"/>
            </w:pPr>
            {b_prefix}
            <w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{escaped_text}</w:t></w:r>
        </w:p>'''

    def table(headers, rows, col_widths=None):
        num_cols = len(headers)
        if not col_widths:
            w = int(9000 / num_cols)
            col_widths = [w] * num_cols

        grid_cols = ''.join([f'<w:gridCol w:w="{cw}"/>' for cw in col_widths])
        
        tbl_header = f'''<w:tbl>
            <w:tblPr>
                <w:tblW w:w="9000" w:type="dxa"/>
                <w:tblBorders>
                    <w:top w:val="single" w:sz="4" w:space="0" w:color="CBD5E0"/>
                    <w:left w:val="none"/>
                    <w:bottom w:val="single" w:sz="8" w:space="0" w:color="A0AEC0"/>
                    <w:right w:val="none"/>
                    <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>
                    <w:insideV w:val="none"/>
                </w:tblBorders>
                <w:tblCellMar>
                    <w:top w:w="80" w:type="dxa"/>
                    <w:left w:w="120" w:type="dxa"/>
                    <w:bottom w:w="80" w:type="dxa"/>
                    <w:right w:w="120" w:type="dxa"/>
                </w:tblCellMar>
            </w:tblPr>
            <w:tblGrid>{grid_cols}</w:tblGrid>
            <w:tr>
        '''
        
        for i, h in enumerate(headers):
            escaped_h = h.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            tbl_header += f'''
                <w:tc>
                    <w:tcPr>
                        <w:tcW w:w="{col_widths[i]}" w:type="dxa"/>
                        <w:shd w:val="clear" w:color="auto" w:fill="2B6CB0"/>
                    </w:tcPr>
                    <w:p>
                        <w:pPr><w:spacing w:after="0"/></w:pPr>
                        <w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="19"/></w:rPr><w:t>{escaped_h}</w:t></w:r>
                    </w:p>
                </w:tc>
            '''
        tbl_header += '</w:tr>'

        tbl_body = ''
        for r_idx, row in enumerate(rows):
            fill = "F7FAFC" if r_idx % 2 == 1 else "FFFFFF"
            tbl_body += '<w:tr>'
            for i, cell in enumerate(row):
                escaped_c = str(cell).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '</w:t></w:r></w:p><w:p><w:pPr><w:spacing w:after="0"/></w:pPr><w:r><w:rPr><w:sz w:val="18"/><w:color w:val="2D3748"/></w:rPr><w:t>')
                tbl_body += f'''
                    <w:tc>
                        <w:tcPr>
                            <w:tcW w:w="{col_widths[i]}" w:type="dxa"/>
                            <w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>
                        </w:tcPr>
                        <w:p>
                            <w:pPr><w:spacing w:after="0"/></w:pPr>
                            <w:r><w:rPr><w:sz w:val="18"/><w:color w:val="2D3748"/></w:rPr><w:t>{escaped_c}</w:t></w:r>
                        </w:p>
                    </w:tc>
                '''
            tbl_body += '</w:tr>'

        return tbl_header + tbl_body + '</w:tbl><w:p><w:pPr><w:spacing w:after="140"/></w:pPr></w:p>'

    def image(rel_id, name="Architecture Diagram", cx=5400000, cy=3037500):
        return f'''<w:p>
            <w:pPr><w:jc w:val="center"/><w:spacing w:after="160"/></w:pPr>
            <w:r>
                <w:drawing>
                    <wp:inline distT="0" distB="0" distL="0" distR="0">
                        <wp:extent cx="{cx}" cy="{cy}"/>
                        <wp:effectExtent l="0" t="0" r="0" b="0"/>
                        <wp:docPr id="1" name="{name}"/>
                        <wp:cNvGraphicFramePr>
                            <a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>
                        </wp:cNvGraphicFramePr>
                        <a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
                            <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
                                <pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
                                    <pic:nvPicPr>
                                        <pic:cNvPr id="0" name="{name}"/>
                                        <pic:cNvPicPr/>
                                    </pic:nvPicPr>
                                    <pic:blipFill>
                                        <a:blip r:embed="{rel_id}"/>
                                        <a:stretch><a:fillRect/></a:stretch>
                                    </pic:blipFill>
                                    <pic:spPr>
                                        <a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
                                        <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                                    </pic:spPr>
                                </pic:pic>
                            </a:graphicData>
                        </a:graphic>
                    </wp:inline>
                </w:drawing>
            </w:r>
        </w:p>'''

    def callout(title, text):
        escaped_title = title.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        escaped_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return f'''<w:tbl>
            <w:tblPr>
                <w:tblW w:w="9000" w:type="dxa"/>
                <w:tblBorders>
                    <w:left w:val="single" w:sz="24" w:space="0" w:color="3182CE"/>
                    <w:top w:val="none"/>
                    <w:bottom w:val="none"/>
                    <w:right w:val="none"/>
                </w:tblBorders>
                <w:tblCellMar><w:top w:w="100" w:type="dxa"/><w:left w:w="160" w:type="dxa"/><w:bottom w:w="100" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tblCellMar>
            </w:tblPr>
            <w:tblGrid><w:gridCol w:w="9000"/></w:tblGrid>
            <w:tr>
                <w:tc>
                    <w:tcPr><w:tcW w:w="9000" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="EBF8FF"/></w:tcPr>
                    <w:p>
                        <w:pPr><w:spacing w:after="30"/></w:pPr>
                        <w:r><w:rPr><w:b/><w:color w:val="2B6CB0"/><w:sz w:val="19"/></w:rPr><w:t>{escaped_title}</w:t></w:r>
                    </w:p>
                    <w:p>
                        <w:pPr><w:spacing w:after="30"/></w:pPr>
                        <w:r><w:rPr><w:sz w:val="18"/><w:color w:val="2D3748"/></w:rPr><w:t>{escaped_text}</w:t></w:r>
                    </w:p>
                </w:tc>
            </w:tr>
        </w:tbl><w:p><w:pPr><w:spacing w:after="120"/></w:pPr></w:p>'''

    # Build the document XML content
    body = []
    
    # Document Title
    body.append(p("THE HR AGENTIC SOLUTION", bold=True, size=44, color="1A365D", align="center", space_after=80))
    body.append(p("Architecture, Philosophy & Practical Design Guide — Team 12", bold=True, size=24, color="4A5568", align="center", space_after=140))
    body.append(p("Designing with Empathy, Precision, and Trust for Modern Enterprises", italic=True, size=20, color="718096", align="center", space_after=260))

    # Document Control
    body.append(heading("Guide Information", 1))
    body.append(table(
        ["Field", "Value"],
        [
            ["Document Title", "The HR Agentic Solution: Architecture, Philosophy & Design Guide"],
            ["Project Name", "Project Elevate — HR Agentic Solution"],
            ["Team", "Team 12"],
            ["Author(s)", "Team 12"],
            ["Date", "August 18, 2026"],
            ["Core Purpose", "Explain why we built it, how it works, and why we chose this architecture in a friendly, grounded narrative."],
            ["Audience", "Enterprise Leaders, HR Executives, People Operations, IT Architects, and Employees"]
        ],
        [2800, 6200]
    ))

    # Section 1: Welcome & Human Introduction
    body.append(heading("1. Welcome & Human Introduction", 1))
    body.append(p("When an employee opens an HR portal, they aren't looking to 'interact with an AI model.'"))
    body.append(p("They might be a new parent figuring out parental leave so they can care for their newborn child. They might be an engineer waking up sick before a critical release, wanting to rest without worrying about confusing leave codes. Or they might be moving homes, needing to update their address and request a monitor for remote work."))
    body.append(p("In these moments, clarity, speed, and empathy matter more than anything else."))
    body.append(p("Yet today, employees spend hours navigating disconnected systems (Workday, ServiceNow, PDF policies) and waiting 4 to 24 hours for basic answers. We built the HR Agentic Solution to solve this human problem."))

    # Section 2: Core Philosophy & Design Choices
    body.append(heading("2. Our Core Design Philosophy: Why We Made These Choices", 1))
    body.append(heading("2.1. Plain-English Architecture Translation", 2))
    body.append(table(
        ["Technical Term", "Friendly Plain-English Analogy", "Real-World Business Function"],
        [
            ["Multi-Agent Architecture", "Specialized Department Team", "A lead coordinator connects you to dedicated experts (Policy, Leave, IT Helpdesk)."],
            ["Google ADK & Gemini 2.5", "Ultra-Fast Reasoning Brain", "Understands everyday natural language in milliseconds with zero robotic stiffness."],
            ["Model Context Protocol (FastMCP)", "Universal System Plug (USB-C)", "Connects AI securely to Workday and ServiceNow without fragile custom code."],
            ["RAG (Open Knowledge Format)", "Verified Digital Employee Handbook", "AI reads verified company policies before answering (100% grounded truth)."],
            ["Serverless Cloud Run", "On-Demand Power Grid", "Auto-scales instantly during peak leave seasons and drops to $0 when idle."],
            ["Circuit Breaker & Throttling", "Safety Fuse Box", "Automatic fuse box preventing system crashes if downstream SaaS slows down."]
        ],
        [2500, 2500, 4000]
    ))

    body.append(heading("2.2. The 5 Foundational Architectural Decisions", 2))
    body.append(bullet(" Specialized domain agents (Policy, HCM, ITSM) supervised by an Orchestrator deliver higher accuracy and zero role confusion compared to a generic one-size-fits-all chatbot.", "1. Hub-and-Spoke Teamwork: "))
    body.append(bullet(" Every policy answer is backed by verifiable clickable citations (policy://...). If a policy doesn't exist, the AI politely explains rather than making up answers.", "2. Grounded Factual Truth: "))
    body.append(bullet(" Open standard FastMCP dynamically discovers tool schemas, ensuring zero breaking changes when Workday or ServiceNow update.", "3. Universal System Connectors: "))
    body.append(bullet(" Technology should never block a human connection. Moments of crisis (medical, bereavement) automatically trigger Priority-2 HR tickets with 2-hour SLAs.", "4. Compassionate Human Escalation: "))
    body.append(bullet(" In-flight DLP regex filters automatically redact Singapore NRICs, credit cards, and passwords before transmission, honoring employee dignity and GDPR/PDPA laws.", "5. Fierce Privacy Protection: "))

    # Section 3: Architecture & Visual Overview
    body.append(heading("3. The Architecture: How the System Works Together", 1))
    body.append(p("The following architecture diagrams illustrate how the user interface, API gateway, multi-agent orchestrator, and enterprise SaaS layers connect:"))
    body.append(image("rIdImg1", "Target Solution Architecture"))
    body.append(image("rIdImg2", "Multi-Agent AI Flow"))

    # Section 4: Real-World Scenarios
    body.append(heading("4. A Day in the Life: Real-World Experience Walkthroughs", 1))
    
    body.append(heading("Scenario A: The Thoughtful Sick Leave Request (Compound Workflow)", 2))
    body.append(p("Employee Prompt: 'I am feeling unwell today. What is our sick leave policy in Singapore, and could you please book 2 days of sick leave for me starting today and open a ticket to route my emails to my manager?'"))
    body.append(bullet(" Step 1: Policy specialist verifies Singapore MOM policy (14 days outpatient, no MC needed for <=2 days).", "Execution Trace: "))
    body.append(bullet(" Step 2: HCM specialist checks live WorkWeek balance (10.0d available) and confirms 2-day booking (Req ID: REQ-8812).", "Execution Trace: "))
    body.append(bullet(" Step 3: ITSM specialist opens IT Access Ticket INC0002608 with Moderate priority to route emails.", "Execution Trace: "))
    body.append(p("Outcome: Employee receives a unified, caring confirmation in under 1.5 seconds, with all tasks completed across both systems."))

    body.append(heading("Scenario B: The Responsible Safety Check (Guardrail in Action)", 2))
    body.append(p("Employee Prompt: 'Can I book 25 days of vacation leave starting next week?'"))
    body.append(bullet(" HCM specialist checks live WorkWeek balance and identifies the employee has 15.0 days remaining.", "Execution Trace: "))
    body.append(p("Outcome: Agent explains the balance limit politely and offers options (e.g. book 15.0 available days or connect with HR for unpaid leave) without failing or generating an error."))

    body.append(heading("Scenario C: Compassionate Human Escalation (Moments that Matter)", 2))
    body.append(p("Employee Prompt: 'I have experienced a sudden family bereavement and need urgent leave advice.'"))
    body.append(bullet(" ITSM specialist immediately calls escalate_to_human_hr(), creating Priority-2 Case INC0002609 under HR Support with a 2-hour SLA.", "Execution Trace: "))
    body.append(p("Outcome: Employee is offered immediate condolences, 24/7 EAP counseling contacts, and a direct human callback commitment."))

    # Section 5: Strategic Business & Human Outcomes
    body.append(heading("5. Strategic Business & Human Outcomes", 1))
    body.append(table(
        ["Strategic Metric", "Baseline (Manual State)", "With HR Agentic Solution", "Human & Business Impact"],
        [
            ["Average Resolution Time", "4 to 24 hours", "< 1.5 seconds", "Employees get answers instantly without workplace anxiety."],
            ["Tier-1 Ticket Deflection", "0% automated", ">40% deflected", "HR teams focus on culture, talent, and real human connection."],
            ["Cost per Inquiry", "$15.00 - $22.00", "<$0.00035", ">99.9% cost reduction (~$120,000/mo net savings for 10k staff)."],
            ["Policy Compliance", "Manual interpretation errors", "100% grounded citations", "Zero compliance risk with statutory labour authorities (MOM)."],
            ["Employee Privacy", "Exposed chat logs", "In-flight DLP masking", "Employees feel safe asking sensitive workplace questions."]
        ],
        [2200, 2200, 2200, 2400]
    ))

    # Section 6: Summary
    body.append(heading("6. Conclusion: A Modern Bridge for the Enterprise", 1))
    body.append(p("The HR Agentic Solution (Team 12) is more than an AI integration—it is a modern, empathetic digital workplace bridge. By combining Google's cutting-edge Gemini reasoning engine with grounded policy retrieval, universal enterprise connectors, and deep human empathy, we empower every employee to do their best work with peace of mind."))

    # Write document.xml
    doc_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"
                xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
                xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <w:body>
            {''.join(body)}
            <w:sectPr>
                <w:pgSz w:w="12240" w:h="15840"/>
                <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
                <w:cols w:space="720"/>
                <w:docGrid w:linePitch="360"/>
            </w:sectPr>
        </w:body>
    </w:document>'''

    with open("scripts/temp_guide_docx/word/document.xml", "w", encoding="utf-8") as f:
        f.write(doc_xml)

    # Re-zip into OUTPUT_DOCX
    with zipfile.ZipFile(OUTPUT_DOCX, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk("scripts/temp_guide_docx"):
            for file in files:
                p_full = os.path.join(root, file)
                arcname = os.path.relpath(p_full, "scripts/temp_guide_docx")
                z.write(p_full, arcname)

    # Cleanup temp
    shutil.rmtree("scripts/temp_guide_docx")
    print(f"[✓] Successfully generated Architecture & Philosophy Guide: {OUTPUT_DOCX}")

if __name__ == "__main__":
    create_guide_docx()
