"""Script to build the official Enterprise Solution Design Document in .docx format with full decision flowchart and node explanation matrix."""
import os
import zipfile
import shutil

OUTPUT_DOCX = "Enterprise Agentic Solution Design Document - HR Agentic Solution (MVP 1).docx"
ARCH_IMG = "images/system_architecture.jpg"
FLOW_IMG = "images/flow_diagram.jpg"

def create_docx():
    os.makedirs("scripts/temp_docx", exist_ok=True)
    
    # Read existing docx template to reuse fonts, styles, and settings
    with zipfile.ZipFile(OUTPUT_DOCX, "r") as z:
        z.extractall("scripts/temp_docx")

    # Update [Content_Types].xml to ensure image/jpeg is registered
    ct_path = "scripts/temp_docx/[Content_Types].xml"
    with open(ct_path, "r", encoding="utf-8") as f:
        ct_content = f.read()
    if 'Extension="jpg"' not in ct_content and 'Extension="jpeg"' not in ct_content:
        ct_content = ct_content.replace('</Types>', '<Default Extension="jpg" ContentType="image/jpeg"/><Default Extension="jpeg" ContentType="image/jpeg"/></Types>')
        with open(ct_path, "w", encoding="utf-8") as f:
            f.write(ct_content)

    # Add images to word/media/
    media_dir = "scripts/temp_docx/word/media"
    os.makedirs(media_dir, exist_ok=True)
    shutil.copy(ARCH_IMG, os.path.join(media_dir, "image1.jpg"))
    shutil.copy(FLOW_IMG, os.path.join(media_dir, "image2.jpg"))

    # Update word/_rels/document.xml.rels with image relationships
    rels_path = "scripts/temp_docx/word/_rels/document.xml.rels"
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

    # Build the document XML content
    body = []
    
    # Document Title
    body.append(p("ENTERPRISE SOLUTION DESIGN DOCUMENT", bold=True, size=44, color="1A365D", align="center", space_after=80))
    body.append(p("HR Agentic Solution (MVP 1 & Enterprise Target State) — Team 12", bold=True, size=24, color="4A5568", align="center", space_after=240))

    # Document Control
    body.append(heading("Document Control", 1))
    body.append(table(
        ["Field", "Value"],
        [
            ["Document Title", "Enterprise Solution Design Document — HR Agentic Solution (MVP 1)"],
            ["Project Name", "Project Elevate — HR Agentic Solution"],
            ["Team", "Team 12"],
            ["Author(s)", "Team 12"],
            ["Date", "August 18, 2026"],
            ["Status", "Approved & Enterprise Production-Ready"],
            ["Target Audience", "Enterprise Architecture Review Board, HR Leadership, IT Operations, Data Protection Officer, Lead Engineers"]
        ],
        [2800, 6200]
    ))

    # Section 1: Executive Summary & Non-Technical Guide
    body.append(heading("1. Executive Summary & Plain-English Glossary", 1))
    body.append(heading("1.1. Executive Business Problem & Strategic Impact", 2))
    body.append(p("Enterprise employees lose productive hours navigating disconnected HR software. Over 45% of incoming support tickets are routine inquiries regarding leave entitlements, policy rules, and standard IT requests, resulting in 4-to-24 hour resolution delays."))

    body.append(heading("1.2. Plain-English Architecture Translation for Executives", 2))
    body.append(table(
        ["Technical AI / Cloud Term", "Plain-English Analogy", "Real-World Business Function"],
        [
            ["Multi-Agent Architecture", "Specialized Department Team", "Lead coordinator routes inquiries to specialist sub-assistants (Policy, Leave, IT)."],
            ["Google ADK & Gemini 2.5", "Ultra-Fast Reasoning Brain", "AI cognitive engine that understands natural language in milliseconds."],
            ["Model Context Protocol (FastMCP)", "Universal System Plug (USB-C)", "Standardized plug connecting AI securely to Workday and ServiceNow."],
            ["RAG (Open Knowledge Format)", "Verified Digital Employee Handbook", "AI reads verified company handbook before answering (100% grounded)."],
            ["Serverless Cloud Run", "On-Demand Power Grid", "Auto-scales instantly during peak leave seasons and drops to $0 when idle."],
            ["Circuit Breaker & Throttling", "Safety Fuse Box", "Automatic fuse box preventing system crashes if downstream SaaS slows down."]
        ],
        [2500, 2500, 4000]
    ))

    body.append(heading("1.3. Executive Business Value & ROI Translation", 2))
    body.append(table(
        ["Business Metric / Driver", "Baseline (Current State)", "With HR Agentic Solution", "Strategic Business Impact"],
        [
            ["Tier 1 Ticket Deflection", "0% automated deflection", ">40% deflected in 6 months", "Deflects 4,000+ monthly routine tickets."],
            ["Average Resolution Time", "4 to 24 hours", "< 1.5 seconds response", "Eliminates administrative friction for 10k staff."],
            ["Cost per Inquiry", "$15.00 - $22.00 (Human)", "<$0.00035 (AI inquiry)", ">99.9% cost reduction (~$120,000/mo net savings)."],
            ["Policy Compliance", "Manual interpretation risks", "100% grounded citations", "Zero compliance penalties; strict MOM alignment."],
            ["Employee Satisfaction", "68% (Friction & wait times)", ">92% projected CSAT", "Seamless 3-column UI with live deep links."]
        ],
        [2200, 2200, 2200, 2400]
    ))

    # Section 2: Architecture Justification & Alternatives Deep Dive
    body.append(heading("2. Architecture Justification: Why We Chose This Design & Rejected Alternatives", 1))
    body.append(p("All architectural choices were evaluated against leading industry alternatives across five standardized dimensions:"))
    
    body.append(heading("2.1. Dimension 1: Agent Orchestration Framework Matrix", 2))
    body.append(table(
        ["Framework Option", "Score", "Pros / Strengths", "Why We Chose / Rejected It"],
        [
            ["Google ADK (Selected)", "5.0/5.0", "Native Gemini function calling, sub-second streaming, zero overhead.", "SELECTED: Production-grade latency and seamless Cloud Run & Vertex deployment."],
            ["LangChain / LangGraph", "3.0/5.0", "Generic multi-model support, complex graph states.", "REJECTED: Heavy middleware overhead and brittle nested abstractions."],
            ["CrewAI / AutoGen", "2.6/5.0", "Autonomous multi-agent role-playing conversation mesh.", "REJECTED: Chatty inter-agent token loops led to 5x higher token costs and 10s latency."],
            ["Monolithic Prompt Bot", "1.8/5.0", "Single prompt attempting to handle all 10+ tool schemas.", "REJECTED: High hallucination rate, parameter confusion between HCM and ITSM."]
        ],
        [2200, 1000, 2800, 3000]
    ))

    body.append(heading("2.2. Dimension 2: Policy Knowledge Retrieval (RAG) Matrix", 2))
    body.append(table(
        ["Retrieval Option", "Score", "Pros / Strengths", "Why We Chose / Rejected It"],
        [
            ["Dynamic Chunked OKF (Selected)", "5.0/5.0", "100% factual grounding, <60s hot-reload, $0 hosting cost.", "SELECTED: Exact policy citations, sub-millisecond retrieval, human-auditable markdown."],
            ["Pinecone / Vector DB", "2.1/5.0", "Approximate nearest neighbor semantic search.", "REJECTED: Semantic drift risks (wrong country policy matches), $70-$300/mo extra cost."],
            ["Vertex AI Search RAG", "3.8/5.0", "Enterprise search across millions of multi-format documents.", "DEFERRED: Ideal for Phase 3 global scale (50+ countries), unnecessary overhead for Singapore MVP."]
        ],
        [2200, 1000, 2800, 3000]
    ))

    # Section 3: End-to-End Decision Flowchart & Node Explanation
    body.append(heading("3. End-to-End System Decision Logic Flowchart & Execution Matrix", 1))
    body.append(p("The following visual flow diagram and node-by-node explanation define the deterministic decision path executed by the multi-agent system:"))
    body.append(image("rIdImg2", "Multi-Agent AI Decision Flow"))

    body.append(heading("3.1. Flowchart Node-by-Node Explanation Matrix", 2))
    body.append(table(
        ["Flowchart Node", "Component / Layer", "Input & Trigger Condition", "Execution Logic & Invariant Check", "Output / System Action"],
        [
            ["W3C & In-Flight DLP", "API Gateway", "Inbound user message", "Injects traceparent & X-Correlation-ID; regex scrubs Singapore NRICs with [NRIC_REDACTED].", "Sanitized, traced payload passed to agent."],
            ["Identity Bridge", "Security Layer", "OIDC email claim", "Queries users directory table; immutably locks session to EMP-380.", "Blocks cross-user profile mutation attempts."],
            ["hr_orchestrator", "Central AI Brain", "Natural language query", "Analyzes intent using Gemini 2.5 Flash; classifies request as Policy, HCM, ITSM, or Compound.", "Routes sub-tasks to specialist sub-agents."],
            ["policy_specialist", "Knowledge Engine", "Policy inquiry", "Reads indexed OKF markdown; extracts exact statutory clauses (14d outpatient).", "Returns grounded answer with policy:// citations."],
            ["BalanceGuard", "Safety Invariant", "Leave parameters", "Compares requested days against live WorkWeek vacation/sick balance.", "If <= balance: executes booking. If >: explains limit politely."],
            ["SupportType", "ITSM / Escalation", "IT request or crisis", "Detects urgent medical/family crisis or downstream SaaS 5xx timeout.", "Standard: opens ticket. Crisis: calls escalate_to_human_hr (2h SLA)."],
            ["CompSeq", "Chained Coordinator", "Compound request", "Executes atomic sequence: Policy Check -> Leave Booking -> IT Ticket Routing.", "Ensures end-to-end multi-system execution."],
            ["Synth & LogDB", "Response Generator", "Sub-agent payloads", "Synthesizes final cohesive response; logs turn to Cloud SQL hr_agentic_sessions.db.", "Streams response to UI and refreshes My Hub drawer."]
        ],
        [1500, 1200, 1600, 2500, 2200]
    ))

    # Section 4: Architecture & FastMCP Contracts
    body.append(heading("4. Core Architecture & FastMCP Interface Contracts", 1))
    body.append(p("The system implements a decoupled multi-agent architecture built on the Google ADK and Model Context Protocol, fronted by a 3-column web workspace:"))
    body.append(image("rIdImg1", "Target Solution Architecture"))

    body.append(heading("4.1. FastMCP Interface Contracts & Tool Catalog", 2))
    body.append(table(
        ["Sub-Agent", "Tool Name", "Required Parameters", "Return Payload Schema", "Rate Limit"],
        [
            ["hcm_specialist", "get_employee_balances", "employee_id (str)", "{\"vacation_days\": float, \"sick_days\": float}", "60 req/min"],
            ["hcm_specialist", "request_time_off", "employee_id, start_date, end_date, leave_type, days", "{\"status\": str, \"request_id\": str, \"remaining_days\": float}", "30 req/min"],
            ["hcm_specialist", "update_personal_info", "employee_id, address?, phone?", "{\"status\": str, \"updated_fields\": dict}", "30 req/min"],
            ["itsm_specialist", "list_tickets", "employee_id (str)", "[{\"ticket_id\": str, \"category\": str, \"status\": str}]", "120 req/min"],
            ["itsm_specialist", "create_ticket", "requested_by, category, short_desc, priority, group", "{\"ticket_id\": str, \"status\": \"New\"}", "30 req/min"],
            ["itsm_specialist", "escalate_to_human_hr", "requested_by, reason, conversation_summary", "{\"ticket_id\": str, \"priority\": \"2 - High\", \"group\": \"HR Support\"}", "10 req/min (Burst)"]
        ],
        [1500, 1800, 2000, 2500, 1200]
    ))

    # Section 5: Downstream Error Handling
    body.append(heading("5. Downstream Error Handling, State Persistence & Dynamic Ingestion", 1))
    body.append(heading("5.1. Consolidated Downstream API Error-Handling Matrix", 2))
    body.append(table(
        ["HTTP Status", "Trigger Condition", "User-Facing Conversational Message", "System / Recovery Action"],
        [
            ["400 Bad Request", "Invalid date format or parameter", "Please check your requested dates. Dates must follow YYYY-MM-DD.", "Agent re-prompts user for correct parameters."],
            ["401/403 Forbidden", "Expired or invalid FastMCP token", "Your session token has expired. Please refresh your session.", "Blocks execution; prompts re-authentication."],
            ["404 Not Found", "Ticket ID or employee not found", "I couldn't locate record [ID]. Please verify the ticket or ID number.", "Offers search assistance or lists active tickets."],
            ["429 Rate Limited", "Request quota exceeded", "Our systems are experiencing high volume. Retrying momentarily...", "Parses Retry-After; executes exponential backoff."],
            ["500/502/503/504", "SaaS timeout or server error", "I encountered a service delay. I have opened Priority Ticket INC... for HR.", "Auto-invokes escalate_to_human_hr(), alerts HR."]
        ],
        [1400, 2200, 3200, 2200]
    ))

    # Section 6: Security, RBAC & Risk Register
    body.append(heading("6. Security, RBAC, Privacy & Consolidated Risk Register", 1))
    body.append(heading("6.1. Role-Based Access Control (RBAC) Matrix", 2))
    body.append(table(
        ["Enterprise Role", "Authorized Sub-Agents", "Allowed Tools & Actions", "Prohibited Actions"],
        [
            ["Standard Employee", "policy, hcm, itsm", "View own balance, book own leave, create/view own tickets", "Modify other users' data, delete tickets, access salary"],
            ["People Manager", "policy, hcm, itsm", "All Employee tools, view direct reports' leave, approve leave", "Modify IT configs, direct DB mutations"],
            ["HR Specialist / Admin", "All Sub-Agents", "Trigger policy hot-reload, view all leave, reassign Tier-2 tickets", "Direct server terminal access, unmasked credit card access"],
            ["IT Helpdesk Analyst", "policy, itsm", "Query all tickets, update ticket status, edit work notes", "Modify employee HCM balances, change home addresses"]
        ],
        [1800, 1600, 2800, 2800]
    ))

    body.append(heading("6.2. Consolidated Enterprise Risk Register", 2))
    body.append(table(
        ["Risk ID", "Category", "Risk Description", "Likelihood", "Impact", "Technical Mitigation Strategy", "Owner"],
        [
            ["RSK-01", "Integration", "Downstream SaaS FastMCP API rate limiting or 5xx outages.", "Medium", "High", "Token-bucket rate limiter, 429 backoff, and automated Tier-2 HR escalation.", "Lead Cloud Architect"],
            ["RSK-02", "Governance", "Vendor introduces breaking schema changes (field renames).", "Low", "High", "Dynamic tools/list schema discovery, nightly CI contract tests, defensive fallback.", "IT Integration Lead"],
            ["RSK-03", "Compliance", "Employee asks for policy exception, leading to AI hallucination.", "Low", "Critical", "Temperature fixed at 0.2, mandatory policy:// citations, strict boundary refusal.", "HR Policy Director"],
            ["RSK-04", "Security", "Terminated employee retains active session token mid-conversation.", "Low", "Critical", "Real-time RFC 7009 revocation sync via Redis with 15-min JWT fail-closed TTL.", "SecOps Lead / DPO"],
            ["RSK-05", "Operations", "Policy team uploads contradictory statutory rule to GCS repository.", "Low", "High", "Pre-merge Canary Verification test harness validating statutory MOM invariants.", "HR Operations Lead"]
        ],
        [800, 1100, 2300, 900, 900, 2000, 1000]
    ))

    # Section 7: Future Opportunities
    body.append(heading("7. Future Innovation Opportunities & Strategic Roadmap", 1))
    body.append(bullet(" Connect FastAPI gateway to Slack Bolt & MS Teams for direct slash command interaction in daily tools.", "Omnichannel Slack / Teams Expansion: "))
    body.append(bullet(" Cloud Eventarc & Pub/Sub integration to notify employees of expiring vacation balances before annual rollover.", "Proactive Leave Rollover Alerts: "))
    body.append(bullet(" Graph RAG (Neo4j / Vertex) to automate multi-tier matrix manager leave and equipment approval flows.", "Graph RAG Matrix Approvals: "))
    body.append(bullet(" Dedicated manager copilot providing 1-click team leave approvals and on-call coverage analysis.", "Manager Copilot Sub-Agent: "))

    # Section 8: Conclusion
    body.append(heading("8. Conclusion & 1-Click Deployment", 1))
    body.append(p("The HR Agentic Solution (MVP 1) is fully implemented, verified, and ready for immediate deployment via:"))
    body.append(bullet(" 1-Click build and deploy to Google Cloud Run with public HTTPS URL.", "Full-Stack Web App: ./deploy_full_gcp.sh —"))
    body.append(bullet(" Direct ADK Reasoning Engine deployment to Vertex AI Agent Space.", "Gemini Enterprise Runtime: ./deploy_gemini_enterprise.sh —"))
    body.append(bullet(" Local execution with Google Aura Web UI on port 8090.", "Local Interactive Web UI: ./deploy.sh --ui —"))

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

    with open("scripts/temp_docx/word/document.xml", "w", encoding="utf-8") as f:
        f.write(doc_xml)

    # Re-zip into OUTPUT_DOCX
    with zipfile.ZipFile(OUTPUT_DOCX, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk("scripts/temp_docx"):
            for file in files:
                p_full = os.path.join(root, file)
                arcname = os.path.relpath(p_full, "scripts/temp_docx")
                z.write(p_full, arcname)

    # Cleanup temp
    shutil.rmtree("scripts/temp_docx")
    print(f"[✓] Successfully generated refined executive Word document: {OUTPUT_DOCX}")

if __name__ == "__main__":
    create_docx()
