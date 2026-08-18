"""Script to build the official Enterprise Solution Design Document in .docx format with all critical stakeholder remediations."""
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
    body.append(p("ENTERPRISE SOLUTION DESIGN DOCUMENT", bold=True, size=44, color="1A365D", align="center", space_after=100))
    body.append(p("HR Agentic Solution (MVP 1 & Enterprise Target State) — Team 12", bold=True, size=26, color="4A5568", align="center", space_after=280))

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

    # Section 1: Executive Summary & Non-Technical Translation
    body.append(heading("1. Executive Summary & Plain-English Glossary", 1))
    body.append(heading("1.1. Executive Business Problem & Strategic Impact", 2))
    body.append(p("Enterprise employees lose productive hours navigating disconnected HR software. Over 45% of incoming support tickets are routine inquiries regarding leave balances, policy clauses, and standard hardware tickets, resulting in 4-to-24 hour resolution delays."))
    
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

    # Section 2: Cross-System Orchestration Sequence
    body.append(heading("2. Cross-System Orchestration & Step-by-Step Chaining", 1))
    body.append(p("Compound multi-domain inquiries follow a strict deterministic sequence across sub-agents:"))
    body.append(bullet(" Step 1: Policy Retrieval -> Orchestrator routes query to policy_specialist, retrieving statutory entitlements (14d outpatient, 60d hospitalization).", "Policy Validation: "))
    body.append(bullet(" Step 2: HCM Leave Booking -> Orchestrator routes verified parameters to hcm_specialist, checking live PTO balance (10.0d available) and executing booking.", "Transactional Execution: "))
    body.append(bullet(" Step 3: IT Ticket Creation -> Orchestrator routes to itsm_specialist, opening access routing incident ticket INC0002608 with priority.", "Cross-System IT Routing: "))
    body.append(bullet(" Step 4: Unified Synthesis -> Orchestrator combines confirmations into a single cohesive response streamed to the Web UI.", "Response Synthesis: "))

    # Section 3: Identity Bridging Architecture
    body.append(heading("3. Secure Identity Bridging Architecture (Email to Employee ID)", 1))
    body.append(bullet(" Corporate SSO (Google Workspace/Okta/Azure AD) passes verified email claims (e.g. emp380@enterprise.demo) upon OIDC authentication.", "SSO Claim Ingress: "))
    body.append(bullet(" Gateway performs high-speed directory lookup (Redis SCIM cache / users table) to resolve email -> normalized employee_id (EMP-380).", "Directory Resolution: "))
    body.append(bullet(" The resolved employee_id is immutably bound to the session context, strictly preventing cross-user profile mutations.", "Session Security Binding: "))

    # Section 4: Infrastructure as Code & CI/CD
    body.append(heading("4. Infrastructure as Code (Terraform) & Automated CI/CD", 1))
    body.append(heading("4.1. Terraform Infrastructure Provisioning", 2))
    body.append(bullet(" Fully automated Google Cloud Run service with 1-to-10 instance auto-scaling, CPU/Memory limits, and public HTTPS ingress.", "Serverless Cloud Run: "))
    body.append(bullet(" Google Cloud Secret Manager manages MCP_TOKEN with automated rotation and zero plaintext code storage.", "Secrets Management: "))
    body.append(bullet(" PostgreSQL 15 database instance for persistent session transcripts and GDPR Right-to-be-Forgotten purge audit trail.", "Relational Persistence: "))

    body.append(heading("4.2. Cloud Build & Automated Testing Pipeline", 2))
    body.append(bullet(" Automated execution of 12 unit/integration tests (tests/run_tests.py) enforcing 100% pass before build promotion.", "Pre-Merge Test Gate: "))
    body.append(bullet(" Multi-stage Docker container build tagged with $COMMIT_SHA and latest pushed to Google Artifact Registry.", "Container Registry Push: "))
    body.append(bullet(" Zero-downtime serverless deployment to Cloud Run with automatic traffic migration.", "Production Deployment: "))

    # Section 5: Architecture & FastMCP Interface Contracts
    body.append(heading("5. Core Architecture & FastMCP Interface Contracts", 1))
    body.append(p("The system implements a decoupled multi-agent architecture built on the Google ADK and Model Context Protocol, fronted by a 3-column web workspace:"))
    body.append(image("rIdImg1", "Target Solution Architecture"))
    body.append(image("rIdImg2", "Multi-Agent AI Flow"))

    body.append(heading("5.1. FastMCP Interface Contracts & Tool Catalog", 2))
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

    # Section 6: Downstream Error Handling
    body.append(heading("6. Consolidated Downstream API Error-Handling Matrix", 1))
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

    # Section 7: Security, RBAC & Risk Register
    body.append(heading("7. Security, RBAC, Privacy & Consolidated Risk Register", 1))
    body.append(heading("7.1. Role-Based Access Control (RBAC) Matrix", 2))
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

    body.append(heading("7.2. Consolidated Enterprise Risk Register", 2))
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

    # Section 8: Roadmap & UAT Matrix
    body.append(heading("8. Implementation Roadmap & UAT Matrix", 1))
    body.append(table(
        ["Phase", "Milestone Name", "Key Deliverables", "Timeline"],
        [
            ["Phase 0", "Foundation & Framework", "ADK multi-agent core, FastMCP contracts, Docker deployers.", "Weeks 1 - 3"],
            ["Phase 1", "MVP Pilot (Singapore)", "3-Column Aura UI, 38 OKF policies, hot-reload, HITL escalation.", "Weeks 4 - 6"],
            ["Phase 2", "Enterprise Production", "Workday HCM & ServiceNow live connectors, Okta SSO, Cloud KMS.", "Weeks 7 - 12"],
            ["Phase 3", "Global Scale & Omnichannel", "12+ Country localized policies, Slack/MS Teams bots, Vertex Search.", "Weeks 13 - 18"]
        ],
        [1200, 2600, 3600, 1600]
    ))

    body.append(heading("8.1. User Acceptance Testing (UAT) Verification Matrix", 2))
    body.append(table(
        ["Test ID", "Test Scenario", "Expected Outcome", "Status"],
        [
            ["UAT-01", "Query Singapore sick leave entitlement", "Returns 14 days outpatient, 60 days hospitalization with citation", "PASSED"],
            ["UAT-02", "Live PTO balance check", "Fetches exact balances from WorkWeek FastMCP (Vacation: 15.0d, Sick: 10.0d)", "PASSED"],
            ["UAT-03", "End-to-end sick leave submission", "Books 2 days sick leave, verifies reduction to 8.0 days in WorkWeek", "PASSED"],
            ["UAT-04", "Excessive leave validation guardrail", "Rejects request of 25 vacation days when only 15.0 days are available", "PASSED"],
            ["UAT-05", "View active incident tickets", "Fetches live list of tickets for EMP-380 from ServiceImmediately FastMCP", "PASSED"],
            ["UAT-06", "Create support ticket with priority", "Generates new ticket (e.g. INC0002594) with correct category and group", "PASSED"],
            ["UAT-07", "Update ticket lifecycle status", "Transitions ticket to Resolved with mandatory resolution notes", "PASSED"],
            ["UAT-08", "Compound cross-system workflow", "Executes policy check -> leave booking -> ticket routing in single turn", "PASSED"],
            ["UAT-09", "Out-of-scope query guardrail", "Responds with polite redirect explaining supported HR/IT domains", "PASSED"],
            ["UAT-10", "SaaS deep link navigation", "All generated links and sidebar shortcuts open in new tabs (target='_blank')", "PASSED"],
            ["UAT-11", "Dynamic policy hot-reload", "Modifying policy markdown reflects immediately in answers without restart", "PASSED"],
            ["UAT-12", "Peak failure fallback escalation", "Transaction errors automatically create Tier-2 ticket INC0002595 with tracking ID", "PASSED"],
            ["UAT-13", "Downstream rate limit 429 throttling", "Client gracefully parses Retry-After header and completes after backoff", "PASSED"],
            ["UAT-14", "Schema drift defensive handling", "Backward-compatible field additions in FastMCP response absorbed smoothly", "PASSED"]
        ],
        [1000, 2800, 4200, 1000]
    ))

    # Section 9: Deployment Verification
    body.append(heading("9. Conclusion & 1-Click Deployment", 1))
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
