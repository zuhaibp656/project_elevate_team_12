"""Script to build the streamlined Enterprise Solution Design Document in .docx format."""
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
    body.append(p("SOLUTION DESIGN DOCUMENT", bold=True, size=44, color="1A365D", align="center", space_after=100))
    body.append(p("HR Agentic Solution (MVP 1) — Team 12", bold=True, size=26, color="4A5568", align="center", space_after=280))

    # Document Control
    body.append(heading("Document Control", 1))
    body.append(table(
        ["Field", "Value"],
        [
            ["Document Title", "Enterprise Solution Design Document — HR Agentic Solution (MVP 1)"],
            ["Project Name", "Project Elevate — HR Agentic Solution"],
            ["Team", "Team 12"],
            ["Author(s)", "Zuhaib Parvez & Team 12 Architecture Group"],
            ["Date", "August 18, 2026"],
            ["Status", "Approved & Production-Ready"],
            ["Target Audience", "Enterprise Architecture Review Board, HR Leadership, IT Operations, Lead Engineers"]
        ],
        [2800, 6200]
    ))

    # Section 1: Executive Summary
    body.append(heading("1. Executive Summary & Scope", 1))
    body.append(heading("1.1. Business Problem & Objectives", 2))
    body.append(p("Enterprise employees lose hours navigating disconnected systems (HCM, ITSM, static PDF portals) for basic HR tasks. Over 45% of HR/IT tickets are repetitive inquiries regarding leave balances, policy clauses, and standard IT requests."))
    body.append(callout("Core Objectives", "• Deflect >40% of Tier 1 Inquiries: Instant self-service across Policies, WorkWeek, and ServiceImmediately.\n• Sub-Second Execution: Complete multi-step workflows (Policy -> Leave -> Ticket) in <1.5s.\n• 100% Grounded Answers: Zero hallucinated rules; all policy answers include verifiable markdown citations.\n• Continuous Policy Freshness: Dynamic hot-reloading reflects statutory updates in <60s with verification.\n• Peak Resiliency & HITL: Multi-tier fallback automatically creates tracked human HR escalation tickets."))

    body.append(heading("1.2. Scope Boundaries", 2))
    body.append(table(
        ["Dimension", "In-Scope (MVP 1)", "Target State (Phase 2 / 3)"],
        [
            ["Target Systems", "• WorkWeek FastMCP (/work-week/mcp/)\n• ServiceImmediately FastMCP (/service-immediately/mcp/)\n• Dynamic Singapore Policy Knowledge Base (38 Categories)", "• Production Workday HCM Gateway\n• Production ServiceNow ITSM API\n• Vertex AI Search Enterprise RAG"],
            ["User Interfaces", "• 3-Column Modern Web Workspace (Google Aura)\n• Google ADK Web View (adk web)\n• Terminal CLI Session (deploy.sh --cli)", "• Native Slack & Microsoft Teams Bots\n• Intranet Embedded Chat Widget"],
            ["Identity & Security", "• FastMCP Token Authorization (X-MCP-Token)\n• Google Cloud ADC IAM Authorization\n• Dynamic session identity mapping (EMP-380)", "• Enterprise Okta / Entra ID SSO (OIDC/SAML)\n• RFC 8693 Token Exchange (OBO)\n• RFC 7009 Real-time Revocation Blacklist"]
        ],
        [2000, 3500, 3500]
    ))

    # Section 2: Core Architectural Design Choices
    body.append(heading("2. Core Architectural Design Choices: The 'Why' & 'How'", 1))
    body.append(bullet(" Prevents context pollution and tool hallucinations by isolating specialized domain tools inside dedicated sub-agents. Root orchestrator evaluates intent and coordinates workflows.", "Hub-and-Spoke Orchestration (Google ADK): "))
    body.append(bullet(" Sub-second latency (<400ms TTFT), superior function calling accuracy, massive context window (1M+ tokens), and sub-cent economics (<$0.00035 per query). Temperature 0.2.", "Gemini 2.5 Flash Foundation Model: "))
    body.append(bullet(" Standardizes self-describing tool schemas via JSON-RPC 2.0 and cleanly bypasses Google Cloud IAP browser popups using programmatic X-MCP-Token headers.", "FastMCP Integration Protocol: "))
    body.append(bullet(" Zero vector DB hosting fees and sub-millisecond retrieval. Directory mtime tracking and Eventarc webhooks with Atomic Double-Buffered Cache (RWMutex) prevent stale reads during updates.", "Dynamic Policy Ingestion & Grounding: "))
    body.append(bullet(" If automated transactions fail, escalate_to_human_hr() automatically creates a Priority 2 HR ticket in ServiceImmediately, passing the full transcript and starting a 2-Hour SLA Timer.", "Peak Resiliency & Human Escalation (HITL): "))
    body.append(bullet(" WorkWeek (60 r/m read / 30 r/m write); ServiceImmediately (120 r/m read / 30 r/m write). Circuit breaker trips after 5 failures. Dynamic schema introspection auto-absorbs optional fields.", "API Throttling & Schema Drift Plan: "))

    # Section 3: Target Architecture
    body.append(heading("3. Target Solution Architecture & Flow", 1))
    body.append(p("The system implements a decoupled multi-agent architecture built on the Google ADK and Model Context Protocol, fronted by a 3-column web workspace:"))
    body.append(image("rIdImg1", "Target Solution Architecture"))
    body.append(image("rIdImg2", "Multi-Agent AI Flow"))

    # Section 4: Sub-Agent Roles
    body.append(heading("4. Sub-Agent Responsibilities & Orchestrated Workflow", 1))
    body.append(table(
        ["Sub-Agent", "Primary Role", "Core Tools", "Output Standards"],
        [
            ["hr_orchestrator", "Central Router & Synthesizer", "Sub-agent delegation", "Structured answers, multi-system coordination, direct tool deep-links, fallback coordination."],
            ["policy_specialist", "Grounded Policy Analyst", "list_concepts, read_concept, refresh_policy_index", "100% grounded citations (policy://...), version & effective date reporting, zero hallucinations."],
            ["hcm_specialist", "WorkWeek Core HR Operator", "get_balances, request_time_off, get_personal_info, update_personal_info, cancel_leave", "Real-time balance verification, leave validation, profile updates, [Open in WorkWeek] links."],
            ["itsm_specialist", "Service Desk Operator", "list_tickets, get_ticket_details, create_ticket, update_ticket_status, escalate_to_human_hr", "Complete ticket profiles (ID, Category, Priority, Status), state machine enforcement, Tier-2 escalation."]
        ],
        [1800, 2200, 2400, 2600]
    ))

    # Section 5: Security, Governance & Tracing
    body.append(heading("5. Security, Governance, Data Lifecycle & Tracing", 1))
    body.append(bullet(" Sessions dynamically bound to authenticated employee IDs (EMP-380). FastMCP passes verified X-MCP-Token headers. Secrets stored in Google Cloud Secret Manager with Cloud KMS (CMEK).", "Security & Identity Binding: "))
    body.append(bullet(" W3C traceparent and X-Correlation-ID headers flow across Web UI -> Gateway -> Orchestrator -> Sub-Agents -> FastMCP -> Cloud Trace for end-to-end flame graph visibility.", "Distributed Tracing: "))
    body.append(bullet(" In-process exponential retries (2 attempts) -> Cloud Tasks / Pub/Sub queue buffer (5 attempts) -> Dead Letter Queue with automated Tier-2 HR escalation ticket creation.", "5xx Error Queuing & DLQ: "))
    body.append(bullet(" Chat transcripts retained 90 days in Cloud SQL; tool execution logs retained 7 years in encrypted GCS audit vault; sensitive SPII scrubbed in-flight prior to DB writes.", "Data Retention (PDPA / GDPR): "))

    # Section 6: Roadmap, FinOps & UAT
    body.append(heading("6. Implementation Roadmap, FinOps & UAT Matrix", 1))
    body.append(heading("6.1. 4-Phase Delivery Roadmap", 2))
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

    body.append(heading("6.2. FinOps & Operational Cost Analysis", 2))
    body.append(table(
        ["Cost Metric", "Value / Unit Cost", "Impact"],
        [
            ["Total LLM Cost per Inquiry", "$0.000265 (~0.026 cents)", "Sub-cent token economics (~1,850 in / 420 out tokens)"],
            ["All-Inclusive Cost per Self-Service Query", "<$0.00035 (~0.035 cents)", ">99.9% cost reduction vs human tier-1 ($15.00)"],
            ["Projected Monthly Savings (10k queries/mo)", "~$120,000 / Month", "Immediate positive ROI in Month 1"]
        ],
        [3200, 3200, 2600]
    ))

    body.append(heading("6.3. User Acceptance Testing (UAT) Verification Matrix", 2))
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

    # Section 7: Deployment Verification
    body.append(heading("7. Conclusion & 1-Click Deployment", 1))
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
