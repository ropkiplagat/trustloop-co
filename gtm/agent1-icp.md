# TrustLoop Africa — ICP Analysis
## Agent 1 Output | Skill: customer-research + gtm-strategy

---

## IDEAL CUSTOMER PROFILES

### ICP-A (Primary): SACCO Loan Manager / Credit Committee Chair
**Firmographics**
- Organisation type: SACCO (Savings & Credit Cooperative)
- Size: 300–8,000 members
- Location: Nairobi, Mombasa, Kisumu, Nakuru — urban-to-peri-urban
- AUM (loan book): KES 10M–500M
- Staff: 5–40 full-time

**Decision-maker profile**
- Title: CEO, Loans Manager, Credit Committee Chairperson, or Finance Manager
- Age: 35–55
- Education: BCom, CPA(K), or Diploma in Cooperative Management
- Tech comfort: mobile-first (M-Pesa power user), basic spreadsheets, WhatsApp for business
- Reports to: Board of Directors / SACCO Supervisory Committee

**Primary Job to Be Done**
> "Approve good loans fast and catch bad ones before they default — without spending 3 days chasing payslips."

**Trigger Events**
1. NPL (non-performing loan) ratio crosses internal threshold (>5%) → board pressure
2. Member complains loan took 2 weeks — threatens to leave for a competitor digital lender
3. Regulator (SASRA) issues guidance on credit risk management
4. A large default by a member who "looked fine on paper"
5. Competitor SACCO starts offering 24-hour loan decisions

**Top Pain Points**
1. Manual credit review takes 3–14 days (payslips, guarantors, home visits)
2. No visibility into member's M-Pesa behaviour — only sees formal salary slips
3. Loan officers rely on gut feel and personal relationships → inconsistent, gameable
4. High NPL rates (Kenya SACCO average: 6.8%) eroding member dividends
5. Board demands faster portfolio growth but also lower defaults — impossible manually
6. Can't assess informal workers, self-employed, or gig economy members at all

**Desired Outcomes**
- Loan decision in under 30 minutes
- NPL rate below 3%
- More loans approved without more risk
- Board impressed by data-driven portfolio management
- Members get answers same day → retention + word-of-mouth

**Objections**
- "Our members don't trust AI" → reframe: score supports the loan officer, not replaces them
- "We already have a credit policy" → reframe: TrustLoop makes that policy faster to execute
- "We don't collect member M-Pesa data" → reframe: applicant uploads their own statement (self-serve)
- "What about data privacy?" → emphasise encrypted processing, GDPR-aligned, no data sharing
- "Too expensive for our budget" → show cost of one bad loan vs. annual subscription

**Alternatives They Consider**
- Metropol / CRB Africa credit checks (formal credit bureau — misses informal earners)
- Internal Excel scoring model (slow, not scalable)
- Guarantor system (works but creates social tension)
- Doing nothing (most common — high default tolerance until crisis)
- TransUnion Kenya (enterprise-grade, too expensive for small SACCOs)

**Key Vocabulary (exact phrases)**
- "Loan defaults are killing our dividends"
- "We can't tell who's a genuine borrower"
- "M-Pesa is all they have — no payslip"
- "Our loan officer is the bottleneck"
- "SASRA is on our case about NPLs"
- "Members want instant loans like M-Shwari"

**How They Find Solutions Today**
- SACCO annual conferences (KUSCCO, SASRA events)
- WhatsApp groups for SACCO managers
- Referral from other SACCO CEOs (trust-driven)
- Kenya Co-operative Alliance newsletter
- LinkedIn (secondary — growing)

---

### ICP-B (Secondary): Digital Lender / MFI Credit Manager
**Firmographics**
- Organisation: Digital lending startup, MFI, or bank's digital lending unit
- Loan ticket: KES 500 – KES 500,000
- Volume: 50–5,000 loan applications/month
- Stack: already has a loan management system (LMS), needs scoring API

**Decision-maker profile**
- Title: Head of Credit, CTO, Product Manager, or Founder
- Age: 28–45
- Technical: comfortable with APIs, webhooks, dashboards
- Pain: high default rate eroding unit economics; rejection rate too blunt

**Trigger Events**
1. Investor asks "what's your default rate and how do you manage it?"
2. Scaling beyond manual review capacity
3. Current bureau scores miss their thin-file customer base
4. Launch into a new county or demographic with no historical data

**Top Pain Points**
1. CRB scores exclude 60%+ of their target market (unbanked / thin file)
2. Bureau data is stale (90-day lag) — doesn't capture current M-Pesa behaviour
3. Manual review team is the growth bottleneck
4. Building an in-house ML model is 6–12 months and $50K+
5. Current default rates make the portfolio unprofitable at scale

**Desired Outcomes**
- API integration to existing LMS in <1 day
- Score in <30 seconds per applicant
- Lower default rate without reducing approval rate
- Audit trail for regulatory reporting

**Alternatives They Consider**
- Build in-house ML model
- CredoLab (international — expensive)
- Safaricom's M-Pesa score (waitlisted, limited access)
- CRB Africa / Metropol (bureau only — misses unbanked)

---

### ICP-C (Tertiary): Fintech / Banking Product Manager
**Context**: Abraham Korir's network — corporates evaluating TrustLoop as a white-label or API partner.
**Trigger**: Board mandate to serve MSMEs or move down-market to informal sector.
**Deal size**: Enterprise licence — KES 500K–2M/year.
**Sales cycle**: 3–6 months. Needs pilot data, compliance sign-off, and IT security review.

---

## NEGATIVE ICP (Do Not Target)

- SACCOs with <100 members (not enough loan volume to justify)
- Paybill/sachet lenders (too price-sensitive, too small ticket)
- Banks with existing scoring teams (will build in-house)
- NGO microfinance (grant-funded, no commercial P&L sensitivity)

---

## BUYER JOURNEY MAP

| Stage | What ICP-A Does | TrustLoop Touchpoint |
|-------|----------------|----------------------|
| **Unaware** | Accepts high defaults as normal | Thought leadership: "Kenya SACCO Default Rate Report" lead magnet |
| **Problem-aware** | Googles "how to reduce SACCO loan defaults" | SEO blog content, LinkedIn posts |
| **Solution-aware** | Asks at KUSCCO conference, WhatsApp group | Demo video, 1-pager, referral |
| **Considering** | Asks "show me it works for a SACCO like ours" | Live demo with Abraham, pilot offer |
| **Decision** | Needs board approval | ROI calculator, case study, pricing page |
| **Customer** | Onboarding + first 10 scores | Concierge onboarding, WhatsApp support |

---

## TAM / SAM / SOM (Kenya)

| Level | Definition | Number | Revenue Potential |
|-------|-----------|--------|-------------------|
| **TAM** | All registered Kenyan SACCOs + MFIs | ~22,000 SACCOs + 400 MFIs | ~$180M/year |
| **SAM** | Urban/peri-urban SACCOs with active loan books | ~4,500 | ~$36M/year |
| **SOM Year 1** | SACCOs accessible via Abraham's network + digital | 50 | ~$150K ARR |
| **SOM Year 2** | Channel partners + SEO + conference sales | 250 | ~$750K ARR |

*Pricing basis: KES 15,000–50,000/month per SACCO depending on volume*

---

## GTM MODE RECOMMENDATION

**Hybrid: Sales-led (ICP-A) + API-led (ICP-B)**
- ICP-A (SACCOs): Sales-led — Abraham owns. High trust required. Relationship + demo model.
- ICP-B (Digital lenders): API-led — self-serve docs + Rop builds integration.
- Month 1–3: Sales-led only. Abraham demos to 20 SACCOs. Target 5 paying.
- Month 4+: Add API docs, pricing page, self-serve for ICP-B.

---
*Agent 1 complete. Output feeds Agent 2 (branding) and Agent 5 (launch calendar).*
