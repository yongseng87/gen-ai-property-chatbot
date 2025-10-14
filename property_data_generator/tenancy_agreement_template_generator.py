import random
from datetime import datetime, timedelta
from fpdf import FPDF
from fpdf.enums import XPos, YPos  # Import the new enums

def generate_tenancy_agreement(property_type, rental_type, ref_no): # Reduced number of parameters for template generation. These parameters are required for code switching.

    # Set up blank spaces for the variables to be used as template document
    full_ref_no = "_____________________"
    start_date = "_____________________"
    landlord_name = "_____________________"
    landlord_id = "_____________________"
    landlord_address = "_____________________"
    landlord_email = "_____________________"
    tenant_name = "_____________________"
    tenant_id = "_____________________"
    tenant_email = "_____________________"
    rental_address = "_____________________"
    rental_period = "___"
    rental_start_date = "_____________________"
    monthly_rent = "__________"
    bank_account = "_____________________"
    security_deposit = "_______________"
    item_excess = "_____"


    # Function for formatting whole text string as bold text.
    def bold_all(text, pdf, font_size=10):
        pdf.set_font("Helvetica", style='B', size=font_size)
        pdf.write(5, text)
        pdf.set_font("Helvetica", size=font_size)

    # Function for formatting text output with bold text enclosed within ** as demarcator based on split text strings.
    def bold_alt(text, pdf, font_size=10):
        for i in range(len(text)):
            if i % 2 == 0:
                pdf.set_font("Helvetica", size=font_size)
            else:
                pdf.set_font("Helvetica", style='B', size=font_size)
            pdf.write(5, text[i])

    # Function for writing a section of text using 'body' format with spacing 10 after paragraph.
    def body_text(text, pdf, font_size=10):
        bold_alt(text.split('**'), pdf, font_size)
        pdf.ln(10)
        return pdf

    # Function for writing a section of text using 'body' format without spacing after paragraph.
    def body_text_ns(text, pdf, font_size=10):
        bold_alt(text.split('**'), pdf, font_size)
        pdf.ln()
        return pdf

    # Function for writing a section of text using 'header' format with spacing 10 after paragraph.
    def header_text(text, pdf, font_size=10):
        bold_all(text, pdf, font_size)
        pdf.ln(10)
        return pdf

    # Function for writing a section of text using 'subheader' format with spacing 8 after paragraph.
    def subheader_text(text, pdf, font_size=10):
        bold_all(text, pdf, font_size)
        pdf.ln(8)
        return pdf

    # Pre-define all the paragraphs with variables for ease of editing and maintenance
    ref_no_para = f"**Reference No.:** {full_ref_no}"
    disclaimer_para = "**Disclaimer:** This is a general document which may not be appropriate for use in all cases. When in doubt, please seek legal advice. In the event of a dispute, the Landlord/Tenant agree not to hold Sterling Properties Pte Ltd liable, for any changes, amendments, additions and deletions that were made on the standard Tenancy Agreement form that had been done with the consent and agreement of both parties prior to the signing of the agreement."
    ll_name_field = f"**NAME:** {landlord_name}"
    ll_id_field = f"**NRIC:** {landlord_id}"
    ll_add_field = f"**ADDRESS:** {landlord_address}"
    ll_email_field = f"**EMAIL:** {landlord_email}"
    ll_definition = "(hereinafter referred to as the \"LANDLORD\" which expression where the context so admits shall include the Landlord's successors and assigns) of the one part."

    tent_name_field = f"**NAME:** {tenant_name}"
    tent_id_field = f"**NRIC:** {tenant_id}"
    tent_email_field = f"**EMAIL:** {tenant_email}"
    tent_definition = "(hereinafter referred to as the \"TENANT\" which expression where the context so admits shall include the Tenant's successors and assigns) of the other part."

    section1title = "1. RENT"
    section1 = f"The Landlord agrees to let and the Tenant agrees to take all that premises known as **{rental_address}** (hereinafter called the \"Premises\") together with the furniture, fixtures and other effects therein (as more fully described in the Inventory List attached)* for a period of **{rental_period}** months commencing from **{rental_start_date}** (the \"Tenancy Agreement\"), at the monthly rental of S$ **{monthly_rent}**. The Monthly Rent shall be paid monthly without demand in advance and clear of all deductions on or before the 21st day of each calendar month. All payments of Rent shall be made to the account of the Landlord with account number **{bank_account}**. If the payment is by GIRO, evidence of such GIRO arrangement shall be provided by the Tenant to the Landlord within 1 month from the commencement of this Tenancy Agreement."

    section2title = "2. The Tenant hereby agrees with the Landlord as follows:"
    section2ah = "(a) RENT"
    section2a = "To pay the Rent at the times and in the manner aforesaid without any deduction whatsoever."
    section2bh = "(b) SECURITY DEPOSIT"
    if property_type == "LANDED":
        section2b = f"To pay the Landlord a sum of S$ **{security_deposit}** (which is equivalent to 3 month(s) rental) upon signing this Tenancy Agreement to be held by the Landlord as a security deposit for the due performance and observance of the terms and conditions herein. If the Tenant fails to perform and/or comply with any of the conditions of this Tenancy Agreement, the Landlord shall be entitled to deduct such amount from the security deposit to remedy the breach and the balance thereof after deduction shall be refunded without interest to the Tenant within fourteen (14) days from the expiry or termination of the Agreement. The security deposit shall not be utilised by the Tenant to set off any Rent payable under this Agreement."
    else:
        section2b = f"To pay the Landlord a sum of S$ **{security_deposit}** (which is equivalent to 2 month(s) rental) upon signing this Tenancy Agreement to be held by the Landlord as a security deposit for the due performance and observance of the terms and conditions herein. If the Tenant fails to perform and/or comply with any of the conditions of this Tenancy Agreement, the Landlord shall be entitled to deduct such amount from the security deposit to remedy the breach and the balance thereof after deduction shall be refunded without interest to the Tenant within fourteen (14) days from the expiry or termination of the Agreement. The security deposit shall not be utilised by the Tenant to set off any Rent payable under this Agreement."
    if rental_type == "1 BEDROOM" or rental_type == "2 BEDROOM":
        section2ch = "(c) PAYMENT OF OUTGOINGS"
        section2c = "In the event that the Tenant's utility consumption is deemed excessive or significantly above average based on past usage history, the Tenant agrees to reimburse the Landlord for the portion of utility costs attributable to such excessive usage. Determination of excessive usage shall be based on utility bills, meter readings, or other reasonable evidence, and the Tenant shall be notified in writing with supporting documentation. Otherwise, the Landlord shall be responsible for all charges due in respect of any telephone, supply of water, electricity, gas and any water-borne sewerage system and/or other equipment installed at the Premises, including any tax payable thereon."
    else:
        section2ch = "(c) PAYMENT OF OUTGOINGS"
        section2c = "To pay all charges due in respect of any telephone, supply of water, electricity, gas and any water-borne sewerage system and/or other equipment installed at the Premises, including any tax payable thereon."
    section2dh = "(d) DEFECT FREE PERIOD"
    section2d = "The Parties agree that there shall be a defect-free period of **30** days which commences on the first day of the tenancy indicated above or date the Premises is handed over to the Tenant (whichever is later) where the Landlord shall not hold the Tenant responsible for any defects of any item, furniture and/or fittings in the Premises that are identified by the Tenant and brought to the Landlord's attention in writing. The Landlord shall be responsible for rectifying any defects so identified."
    section2eh = "(e) MAINTENANCE OF DEMISED PREMISES"
    section2e = "At the Tenant's own cost and expense keep the interior of the Premises including but not limited to the sanitary and water apparatus, furniture, doors and windows, fixtures and fittings in good and tenantable repair and condition throughout the Term and to replace the same with new ones if damaged, lost or broken, and at the expiry or termination of this Tenancy Agreement, to yield up the Premises to the Landlord in good order and condition (fair wear and tear and damage by fire, lighting, earthquake, flood and acts of God or cause not attributable to the neglect of the Tenant excepted)."
    section2fh = "(f) REPLACEMENT OF BULBS"
    section2f = "To replace electric bulbs and tubes at the Tenant's own expense."
    section2gh = "(g) REPLACEMENT OF ITEMS"
    section2g = f"To replace any other items at the Tenant's own expense up to S$ **{item_excess}** per item. In the event the item is more than S$ **{item_excess}** per item, the initial S$ **{item_excess}** is to be borne by the Tenant and the excess to be borne by the Landlord. For replacement above or below S$ **{item_excess}**, Landlord's approval must be obtained prior to such replacement and the Landlord reserves the right to source for the replacement. Any replacement of built-in wardrobe and cabinets, toilet bowls, wash basin, electrical wires, electrical box, shower glass panel, water heater, air conditioning system, wall structures, window, ceiling due to fair wear and tear shall be at landlord's cost to replace except for the replacement was caused by Tenant's negligence."
    section2hh = "(h) TO INDEMNIFY THE LANDLORD"
    section2h = "To be responsible for and to indemnify the Landlord from and against all claims and demands and against damage occasioned to the Premises or any adjacent or neighboring premises or injury caused to any person by any act, default or negligence of the Tenant or the servants, agents, licensees or invitees, guests of the Tenant. The Landlord shall be under no liability to the Tenant, members of the Tenant's immediate family, or to any other person who may be permitted to enter, occupy or use the premises or any part thereof for accidents, happenings or injuries sustained or for loss of or damage to property goods or chattels in the premises or in any part thereof whether arising from the defects in the premises or the negligence of any servant or agent of the Landlord and the Tenant, and the Tenant shall keep the Landlord fully indemnified against all claims, demands, actions, suits, proceedings, orders, damages, costs, losses and expenses of any nature whatsoever which the Landlord may incur or suffer in connection with the aforesaid."
    section2ih = "(i) MINOR REPAIRS"
    section2i = f"To be responsible for all minor repairs and routine maintenance of the Premises not exceeding S$ **{item_excess}** per job/repair/maintenance per item (excluding aircon units/system, water heater and structural repairs) throughout the term of the Tenancy Agreement. In the event any job/repair/maintenance exceeds S$ **{item_excess}** per item, then the initial S$ **{item_excess}** shall be borne by the Tenant and the excess to be borne by the Landlord. For jobs/repairs/maintenance above S$ **{item_excess}**, Landlord's approval must be obtained prior to them being carried out and the Landlord reserves the right to engage his own contractor. For the avoidance of doubt, the Tenant's covenant to carry out minor repairs shall not include any repairs to any water heater, air conditioning system, built-in wardrobes, cabinet, toilet bowl, wash basin, the ceiling, roof, wall structures, structural/main electrical wiring, electrical box unless where the damage is caused by the Tenant's wilful act or negligence."
    if rental_type == "1 BEDROOM" or rental_type == "2 BEDROOM":
        section2jh = "(j) NO SMOKING"
        section2j = "Neither the Tenant, guests, nor any other person shall be allowed to smoke within the Premises. Tenant agrees to refrain from burning candles or incense, and the use of electronic cigarettes, personal vaporizer, or electronic nicotine delivery system inside the Premises. Any violation shall be deemed a material violation of this Agreement. Tenant understands that smoke from any substance will be considered damage. Damage includes but is not limited to deodorizing, repairing, or replacement of carpet, wax removal, additional paint preparation, replacing of drapes/blinds, countertops, or any other surface damaged due to burn marks and/or smoke damage."
        section2kh = "(k) NO COOKING"
        section2k = "Tenants shall not engage in cooking that emits unusual odors in the leased premises or the common areas. This includes, but is not limited to, cooking with strong spices, deep frying, grilling, or any other cooking method that produces strong odors. Tenants are expected to use the kitchen facilities in a manner that does not disturb other residents or create an unpleasant living environment. Failure to comply with this rule may result in penalties or termination of the lease agreement."
        section2lh = "(l) NO ALTERATIONS"
        section2l = "Not to carry out or permit or suffer to be carried out alterations, additions, drilling, hacking or any changes of whatsoever nature to the Premises."
    else: 
        section2jh = "(j) SERVICE OF AIRCON"
        section2j = "To keep air-conditioning units fully serviced every three months. Cost of repair and replacement (including chemical cleaning and gas top up) to be borne by the Tenant. The chemical cleaning of aircon and the appointment of the contractor shall be notified to the Landlord."        
        section2kh = "(k) MAINTENANCE OF AIRCON"
        section2k = "To keep the air-conditioning units in good and tenantable repair and condition provided. The Tenant shall bear the cost and expense for the repair, replacement or renewal of parts, except for those arising from fair wear and tear."
        section2lh = "(l) NO UNAUTHORISED ALTERATIONS"
        section2l = "Not to carry out or permit or suffer to be carried out alterations, additions, drilling, hacking or any changes of whatsoever nature to the Premises without the prior written consent of the Landlord. The Tenant shall make good such alterations at his own cost and/or expense at the request of the Landlord."
    section2mh = "(m) ACCESS FOR REPAIRS"
    section2m = "To permit the Landlord and its agents, surveyors and workmen with all necessary appliances to enter upon the Premises at all reasonable times by prior appointment mutually agreed by both parties for the purpose of viewing the condition thereof or for doing such works and things as may be required for any repairs, alterations or improvements whether of the Premises or of any parts of any building to which the Premises may form a part of or adjoin."
    section2nh = "(n) ACCESS TO VIEWING (NEW TENANT)"
    section2n = "To permit persons with authority from the Landlord at all reasonable times by prior appointment mutually agreed by both parties to enter and view the Premises for the purpose of taking a new tenant during 2 calendar months immediately preceding the termination or expiry of the Tenancy Agreement."
    section2oh = "(o) ACCESS TO VIEWING (POTENTIAL PURCHASER)"
    section2o = "To permit persons with authority from the Landlord at all reasonable times by prior appointment mutually agreed by both parties to enter and view the Premises whenever the Landlord wants to sell the Premises. The Premises shall be sold subject to this Tenancy Agreement, unless agreed otherwise by the parties."
    if rental_type == "1 BEDROOM" or rental_type == "2 BEDROOM":
        section2ph = "(p) NO ASSIGNMENT/SUBLETTING"
        section2p = "Not to assign, sublet or part with the possession of the Premises or any part thereof."
    else:
        section2ph = "(p) ASSIGNMENT/SUBLETTING"
        section2p = "Not to assign, sublet or part with the possession of the Premises or any part thereof without the prior written consent of the Landlord, whose consent shall not be unreasonably withheld, in the case of a respectable or reputable person or corporation."
    section2qh = "(q) NOT TO CAUSE NUISANCE"
    section2q = "Not to do or permit to be done anything on the Premises which shall be or become a nuisance or annoyance or cause injury to the Landlord or to the inhabitants of the neighbouring premises."
    if property_type == "LANDED":
        section2rh = "(r) USE OF PREMISES"
        section2r = "Premises may be used for small home businesses subject to compliance with prevailing rules and regulations, and not for any illegal or other purposes. In the event of breach, this Tenancy Agreement shall be immediately terminated and the security deposit fully forfeited by the Tenant and will be paid to/confiscated by the Landlord without prejudice to any right of action of the Landlord in respect of any breach or any antecedent breach of this Tenancy Agreement by the Tenant."
    else:
        section2rh = "(r) USE OF PREMISES"
        section2r = "To use the Premises as a private dwelling house only and not for any illegal or other purposes. In the event of breach, this Tenancy Agreement shall be immediately terminated and the security deposit fully forfeited by the Tenant and will be paid to/confiscated by the Landlord without prejudice to any right of action of the Landlord in respect of any breach or any antecedent breach of this Tenancy Agreement by the Tenant."
    section2sh = "(s) DANGEROUS MATERIALS"
    section2s = "Not to keep or permit to be kept on the Premises or any part thereof any materials of a dangerous, explosive or radioactive nature or the keeping of which may contravene any laws or regulations."
    section2th = "(t) NOT TO AFFECT INSURANCE"
    section2t = "Not to do or suffer or permit to be done anything or anything to be kept in the Premises whereby the policy or policies of insurance in respect of the Premises or any part thereof against loss or damage by fire may become void or voidable or whereby the rate of premium thereon may be increased, and to pay the Landlord all sums paid by way of increased premiums and expenses incurred for the Premises due to the Tenant's breach herein."
    section2uh = "(u) TENANT'S INSURANCE"
    section2u = "To insure for Tenant's own personal chattels against theft, loss or damage by fire."
    section2vh = "(v) REGISTERED OCCUPIERS"
    section2v = "To permit only occupiers who are registered herein to occupy the Premises. Substitution, addition or change of occupiers are subject to the prior written permission of the Landlord."
    if rental_type == "1 BEDROOM" or rental_type == "2 BEDROOM":
        section2wh = "(w) NO KEEPING OF PETS"
        section2w = "Not to keep or permit to be kept in the Premises or any part thereof any animal or bird."
    else:
        section2wh = "(w) PETS"
        section2w = "Not to keep or permit to be kept in the Premises or any part thereof any animal or bird legally permitted to be pets without the prior written permission of the Landlord and to comply with any conditions imposed by the Landlord in the event such permission is granted."
    section2xh = "(x) COMPLIANCE WITH LAW, RULES AND REGULATIONS"
    section2x = "To comply and conform at all times and in all respects during the continuance of this Tenancy Agreement with the provisions of all laws, acts, enactments and ordinances and rules, regulations, by-laws, orders and notices made thereunder or made by any other competent authority or the Management Corporation. The Tenant shall bear all summonses or fines whether directly or indirectly caused by the Tenant."
    section2yh = "(y) YIELDING UP"
    section2y = "At the expiration or earlier termination of the Tenancy Agreement to peaceably and quietly deliver up to the Landlord the Premises in like condition as if the same were delivered to the Tenant, fair wear and tear and act of God excepted. No painting required to the walls and ceiling and the tenant shall not be required to re-paint it at end of lease if due to the fair wear and tear. Tenant to arrange same level professional cleaning then return the unit to landlord and also dry clean the curtains."
    section2zh = "(z) HANGING OF PICTURE FRAME"
    section2z = "Not to hack any holes or drive anything whatsoever into the walls or to bore any holes in the ceiling without first having obtained the consent in writing of the landlord except anything reasonably done to hang pictures, painting and the like. The Tenant shall remove the nails, screws and hooks and patch the holes with white putty prior to the expiration of the Tenancy."
    section2aah = "(aa) NO LIABILITY IN RESPECT OF INTERRUPTION OF SERVICES AND ETC"
    section2aa = "The Landlord shall not be liable to the Tenant or any other person in respect of any interruption in any of the services or facilities provided by the Landlord by reason of necessary repair or maintenance of any installation or apparatus or damage thereof or destruction thereof by fire, water, act of God or other causes beyond the control of the Landlord or by reason of mechanical or other defect or breakdown or by reason of a strike of workmen or others or of a shortage of fuel, materials, water or labour."
    if property_type == "CONDO / PRIVATE APARTMENT":
        section2abh = "(ab) COMPLIANCE WITH MANAGEMENT CORPORATION"
        section2ab = "To observe and perform all the by-laws, rules and regulations of the Management Corporation for the time being in force and to pay punctually all contributions, levies, fees and other charges which may be imposed by the Management Corporation from time to time in respect of the Premises or any part thereof."
    elif property_type == "LANDED":
        section2abh = "(ab) CLEANING AND UPKEEP OF PREMISES AND EXTERNAL AREAS"
        section2ab = "The Tenant shall ensure that the Premises and external areas are kept pest/mosquito/rodent-free and in a clean and sanitary condition. The Tenant shall, where necessary to maintain the clean and sanitary condition of the Premises, be responsible for engaging qualified professionals including cleaners and/or exterminators to remedy insect/vermin infestations, mould/mildew build-up or other odours at the Tenant's own expense."

    section3title = "3. IMMIGRATION LAWS AND CHECKS FOR FOREIGN TENANTS/OCCUPIERS"
    section3p1 = "The Tenant shall further comply with the terms and conditions below:"
    section3p2 = "[Note: Long-Term Visit Pass, Student's Pass, and Dependant's Pass will be issued in digital format ONLY from 1 January 2023. Due diligence checks under this clause for such passes will be performed based on the digital copy. For such passes issued before 1 January 2023, the due diligence checks will still be performed based on the original copies.]"
    section3ah = "(a)"
    section3a = "The Tenant shall ensure that the Tenant and/or the occupiers of the Premises are lawfully resident in the Republic of Singapore."
    section3bh = "(b)"
    section3b = "The Tenant further covenants with the Landlord that where any of the Tenant and/or occupier are Singapore Citizens or Permanent Residents, the Tenant shall: (i) Personally verify their original identity cards and/or other identification documents if identity card is not available. (ii) Produce their original identity cards and/or other identification documents if identity card is not available, and provide copies for retention to the Landlord and/or his representing Salesperson. (iii) Together with the occupier, meet (or via video conferencing) the Landlord and/or his representing Salesperson for face-to-face verification. (iv) Inform the Landlord in writing in respect of any change in their citizenship status not less than 14 days prior to such change. If the change cannot be anticipated, to inform the Landlord as soon as practicable upon knowledge of such change."
    section3ch = "(c)"
    section3c = "The Tenant further covenants with the Landlord that where any of the Tenant and/or occupier are foreigners, the Tenant shall: (i) Personally verify from original documentation that they have a valid employment pass, work permit, travel document or other papers granted by the Immigration & Checkpoints Authority, Ministry of Manpower or other relevant government authorities. (ii) Ensure that they are in compliance with all relevant legislation, rules and regulations including the Immigration Act, Employment of Foreign Manpower Act (if applicable) and any other applicable law in the Republic of Singapore which relates to foreign residents. (iii) Produce the following documents and provide copies for retention to the Landlord and/or his representing Salesperson: (1) their original identity cards/passports and other relevant documents evidencing their legal entry into Singapore for their stay/work before the commencement of this Tenancy Agreement; and (2) their original identity cards/passports and other relevant documents evidencing their renewal or extension of their lawful stay/work in Singapore before the expiry thereof. (iv) Together with the occupier, meet (or via video conferencing) the Landlord and/or his representing Salesperson for face-to-face verification. (v) Inform the Landlord in writing in respect of any change in their particulars, immigration status or employment status not less than 14 days prior to such change. If the change cannot be anticipated, to inform the Landlord as soon as practicable upon knowledge of such change."
    section3dh = "(d)"
    section3d = "Where the Tenant notifies the Landlord of a change in occupiers, the Landlord is required to conduct all the necessary due diligence checks in this clause."
    section3eh = "(e)"
    section3e = "Notwithstanding anything herein contained, if at any time during the Term of this Tenancy Agreement, any prohibited immigrant is found on the Premises, this Tenancy Agreement shall be immediately terminated and the security deposit fully forfeited by the Tenant and will be paid to/confiscated by the Landlord without prejudice to any right of action of the Landlord in respect of any breach or any antecedent breach of this Tenancy Agreement by the Tenant."

    section4title = "4. The Landlord hereby agrees with the Tenant as follows:"
    section4ah = "(a) QUIET ENJOYMENT"
    section4a = "The Tenant paying the Rents hereby reserved, performing and observing the terms and conditions herein contained shall peaceably hold and enjoy the Premises during the tenancy without any interruption by the Landlord or any person rightfully claiming under or in trust for the Landlord."
    section4bh = "(b) PAYMENT OF PROPERTY TAX"
    section4b = "To pay all property tax, rates and assessments in respect of the Premises other than those agreed to be paid by the Tenant herein."
    section4ch = "(c) KEEP PREMISES IN GOOD REPAIR"
    section4c = "To keep the roof, ceiling, main structure, walls, floors, internal/embedded wiring and pipes, of the Premises in good and tenantable repair and condition. To execute any repairs, replacement and renewal of the Fixtures and fittings including electrical appliances due to fair wear and tear within seven (14) days upon receipt of notice from the Tenant and bear all cost associated with such repair, replacement or renewal subject to clause 2(i)."
    section4dh = "(d) FIRE INSURANCE"
    section4d = "To insure the Premises against loss or damage by fire and to pay the necessary premium punctually. For the avoidance of doubt, such insurance coverage shall be for the loss and/or damage of the Landlord's property and shall not cover any loss and/or damage of the Tenant's property."
    section4eh = "(e) LETTER OF INTENT"
    section4e = "On or before handover of the premises to the Tenant, the Landlord agrees to supply the items and comply with the offer Covenants as stipulated in the Letter of Intent."
    if rental_type == "1 BEDROOM" or rental_type == "2 BEDROOM":
        section4fh = "(j) SERVICE OF AIRCON"
        section4f = "To keep air-conditioning units fully serviced every three months. Cost of repair and replacement (including chemical cleaning and gas top up) to be borne by the Landlord save where the same are caused by act, neglect or omission on the part of the Tenant or any of it servants, agents, occupiers, contractors, guests and visitors."
        section4gh = "(k) MAINTENANCE OF AIRCON"
        section4g = "To keep the air-conditioning units in good and tenantable repair and condition provided. The Landlord shall bear the cost and expense for the repair, replacement or renewal of parts, except where the damage is caused by the Tenant's wilful act or negligence."

    section5title = "5. PROVIDED ALWAYS and it is hereby agreed as follows:"
    section5ah = "(a) DEFAULT OF TENANT"
    section5a = "If (i) the Rent hereby reserved shall be unpaid for 7 days after being payable (whether formally demanded or not), (ii) the Tenant becomes bankrupt or enter into composition with the Tenant's creditors or suffer any distress or execution to be levied on the Tenant's property, (iii) if the Tenant being a company shall go into liquidation whether voluntary (save for the purpose of amalgamation or reconstruction) or compulsory, (iv) the Premises is used for illegal activities, or (v) prohibited immigrant is found in the Premises, it shall be lawful for the Landlord at any time thereafter to re-enter upon the Premises or any part thereof and thereupon this tenancy shall absolutely terminate but without prejudice to the right of action of the Landlord in respect of any antecedent breach of this Tenancy Agreement by the Tenant."
    section5bh = "(b) INTEREST FOR RENT ARREARS"
    section5b = "In the event the Rent remains unpaid for 7 calendar days after becoming payable (whether formally demanded or not) it shall be lawful for the Landlord to claim an interest at 10% on an annual basis on the amount unpaid calculated from after the date due up to the date of actual payment. The recommended formula which is agreed by both parties will be as follows: monthly rental x 10%/365 (to derive interest for 1 day) x number of days payment is late."
    section5ch = "(c) DIPLOMATIC CLAUSE"
    section5c = f"That if at any time after the expiration of **12** months from the date of the commencement of the Tenancy Agreement, **{tenant_name} ({tenant_id})** shall be: (i) deported from Singapore; or (ii) refused permission by the Singapore Government to work or reside in Singapore; or (iii) transferred or relocated from Singapore to another country. it shall be lawful for the Tenant to determine this tenancy by giving not less than **2** months' notice or paying **2** months' Rent in lieu of such notice. Documentary evidence of (i), (ii) or (iii) shall be provided on or before the last day of the termination date or date of handover."
    section5dh = "(d) REIMBURSEMENT OF PRO-RATA COMMISSION"
    section5d = "If the Tenant lawfully terminates this Tenancy Agreement, or pursuant to the exercise of the diplomatic clause, the Tenant shall reimburse the Landlord commission paid to the agency on a pro-rata basis for the remaining unfulfilled term of the tenancy. Documentary evidence of the agent commission Invoice shall be provided to Tenant. The Landlord has the right, but not the obligation, to deduct such reimbursement of the commission from the security deposit as stipulated by Clause 2 above."
    section5eh = "(e) COMPENSATION FOR LOSS"
    section5e = "If this Tenancy Agreement is terminated by breach, the party in breach shall be liable to compensate the innocent party of the loss suffered as a result of the breach."
    section5fh = "(f) OPTION TO RENEW"
    section5f = "That the Landlord shall on the written request of the Tenant made not less than 2 calendar months before the expiry of the tenancy and PROVIDED there shall not be any breach or non-observance of any of the terms and conditions by the Tenant during the term of the tenancy, the Landlord shall grant to the Tenant a tenancy of the said Premises for a further term of **1** year from the expiration of the tenancy hereby created at the prevailing market Rent and upon the same terms and conditions EXCEPT (i) this Option to Renew and (ii) the diplomatic clause (i.e. there will be no right to exercise diplomatic clause during the renewal TERM unless otherwise agreed by the parties). In the event of renewal or extension of the tenancy, the Landlord, and where applicable, shall pay the agency renewal commission in accordance to the CEA Agreement signed between the relevant parties."
    section5gh = "(g) UNTENANTABILITY OF PREMISES LEADING TO SUSPENSION OF RENT"
    section5g = "In case the Premises or any part thereof shall at any time during the said tenancy be destroyed or damaged by fire, lightning, riot, explosion or any other cause not within the control of the parties so as to be unfit for occupation and use, then and in every such case (unless the insurance money shall be wholly or partially irrecoverable by reason solely or in part of any act of default of the Tenant) the Rent hereby reserved or a just and fair proportion thereof according to the nature and extent of the damage sustained shall be suspended and cease to be payable in respect of any period while the Premises (or part thereof) shall continue to be unfit for occupation and use by reason of such damage."
    section5hh = "(h)  UNTENANTABILITY OF PREMISES LEADING TO TERMINATION OF LEASE"
    section5h = "In case the Premises shall be destroyed or damaged as per the sub-clause above, and if the Landlord or the Tenant so thinks fit, either party shall be at liberty to terminate the tenancy hereby created by notice in writing and upon such notice being given the term hereby created shall absolutely cease and determine but without prejudice to any right of action of either party in respect of any antecedent breach of this Tenancy Agreement by the other party."
    if property_type == "LANDED":
        section5ih = "(i) LAND ACQUISITION / RE-DEVELOPMENT CLAUSE"
        section5i = "In the event the Landlord receives a formal written notice from the relevant authorities for acquisition or redevelopment of the Premises, the Landlord shall be at liberty by giving 3 months' notice in writing to determine the tenancy hereby created and shall refund the security deposit to the Tenant (without interest) and neither party shall have any claims against the other."
    else:
        section5ih = "(i) ENBLOC RE-DEVELOPMENT"
        section5i = "In the event of enbloc redevelopment, the Landlord shall be at liberty by giving 3 months' notice in writing to determine the tenancy hereby created and shall refund the security deposit to the Tenant (without interest) and neither party shall have any claims against the other."
    section5jh = "(j) NON-WAIVER"
    section5j = "If one party breaches or defaults any of the terms and conditions in this Tenancy Agreement, and the other party waives such breach or default, that shall not be construed as a waiver of any similar breach or default in the future. If one party delays or omits to exercise any of its rights in this Tenancy Agreement, the delay or omission shall not operate as a waiver of any breach or default of the other party."
    section5kh = "(k) STAMPING"
    section5k = "The stamp duty on the original and duplicate of this Tenancy Agreement shall be borne by the tenant and paid forthwith."
    section5lh = "(l) GOVERNING LAW"
    section5l = f"Any notice required under this Tenancy Agreement shall be sufficiently served if it is sent by post in a registered letter addressed or via email to the Tenant or the Landlord or other person or persons to be served by name at their address specified herein at the last known place of abode or business. A notice sent by registered letter shall deemed to be given at the time when it ought in due course of post to be delivered at the address to which it is sent. Any notice to landlord must email **{landlord_email}**."
    section5mh = "(m) GOVERNING LAW"
    section5m = "This Tenancy Agreement is governed by the laws of the Republic of Singapore."
    section5nh = "(n) APPROVAL OF MORTGAGE"
    section5n = "The Landlord warrants that where the said Premises is mortgaged or charged or subjected to other encumbrance, the landlord has obtained the prior written consent of the financial institutions for the lease of the said Premises."
    section5oh = "(o) JOINT INSPECTION"
    section5o = "Upon the expiration of the said term or earlier determination thereof, the Tenant shall deliver the said premises in such good and tenantable repair and condition (fair wear and tear excepted) as shall be in accordance with the conditions, covenants and stipulations herein contained and with all locks keys and the furniture and with curtains dry clean to the Landlord after a joint inspection thereof by both parties, and thereafter the Tenant shall not be under any liability whatsoever to the Landlord nor shall the Landlord have any claim against the Tenant in respect of any damage to the said premises other than for damage ascertained at the said joint inspection. During the process of obtaining a mutually agreed quotation till completion of rectification works, the Tenant will not be liable to pay any Gross Rent for the said period."
    section5ph = "(p) REVOCATION BY HDB"
    section5p = "If at any time during the Term, the Housing & Development Board (HDB) revokes or withdraws its consent to the rental in which case the termination of this Agreement shall be without prejudice to any rights and/or liabilities of the Landlord or the Tenant, where relevant, in respect of any antecedent breach of this Agreement which is accruing, has accrued or may accrue."


    # Instantiate a PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title of document
    pdf.set_font("Helvetica", style='B', size=16)
    pdf.cell(0, 10, f"TENANCY AGREEMENT ({property_type})", align='C', border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=10)
    if rental_type == "1 BEDROOM" or rental_type == "2 BEDROOM":
        pdf.write(5, "Note: This lease agreement is for the partial rental of bedrooms only.")
        pdf.ln(10)

    # Header Components
    body_text(ref_no_para, pdf)
    body_text(disclaimer_para, pdf)

    pdf.write(5, "This AGREEMENT is made on the ")
    pdf.set_font("Helvetica", style='BU', size=10)
    pdf.write(5,start_date)
    pdf.ln(10)

    header_text("BETWEEN", pdf)

    body_text_ns(ll_name_field, pdf)
    body_text_ns(ll_id_field, pdf)
    body_text_ns(ll_add_field, pdf)
    body_text_ns(ll_email_field, pdf)
    body_text(ll_definition, pdf)

    header_text("AND", pdf)

    body_text_ns(tent_name_field, pdf)
    body_text_ns(tent_id_field, pdf)
    body_text_ns(tent_email_field, pdf)
    body_text(tent_definition, pdf)

    bold_all("WHEREBY IT IS AGREED as follows:", pdf)
    pdf.ln(10)

    # Detailed clauses for section 1
    header_text(section1title, pdf, 14)
    body_text(section1, pdf, 10)

    # Detailed clauses for section 2
    header_text(section2title, pdf, 14)
    subheader_text(section2ah, pdf, 10)
    body_text(section2a, pdf)
    subheader_text(section2bh, pdf)
    body_text(section2b, pdf)
    subheader_text(section2ch, pdf)
    body_text(section2c, pdf)
    subheader_text(section2dh, pdf)
    body_text(section2d, pdf)
    subheader_text(section2eh, pdf)
    body_text(section2e, pdf)
    subheader_text(section2fh, pdf)
    body_text(section2f, pdf)
    subheader_text(section2gh, pdf)
    body_text(section2g, pdf)
    subheader_text(section2hh, pdf)
    body_text(section2h, pdf)
    subheader_text(section2ih, pdf)
    body_text(section2i, pdf)
    subheader_text(section2jh, pdf)
    body_text(section2j, pdf)
    subheader_text(section2kh, pdf)
    body_text(section2k, pdf)
    subheader_text(section2lh, pdf)
    body_text(section2l, pdf)
    subheader_text(section2mh, pdf)
    body_text(section2m, pdf)
    subheader_text(section2nh, pdf)
    body_text(section2n, pdf)
    subheader_text(section2oh, pdf)
    body_text(section2o, pdf)
    subheader_text(section2ph, pdf)
    body_text(section2p, pdf)
    subheader_text(section2qh, pdf)
    body_text(section2q, pdf)
    subheader_text(section2rh, pdf)
    body_text(section2r, pdf)
    subheader_text(section2sh, pdf)
    body_text(section2s, pdf)
    subheader_text(section2th, pdf)
    body_text(section2t, pdf)
    subheader_text(section2uh, pdf)
    body_text(section2u, pdf)
    subheader_text(section2vh, pdf)
    body_text(section2v, pdf)
    subheader_text(section2wh, pdf)
    body_text(section2w, pdf)
    subheader_text(section2xh, pdf)
    body_text(section2x, pdf)
    subheader_text(section2yh, pdf)
    body_text(section2y, pdf)
    subheader_text(section2zh, pdf)
    body_text(section2z, pdf)
    subheader_text(section2aah, pdf)
    body_text(section2aa, pdf)
    if property_type != "HDB FLAT":
        subheader_text(section2abh, pdf)
        body_text(section2ab, pdf)

    # Detailed clauses for section 3
    header_text(section3title, pdf, 14)
    body_text_ns(section3p1, pdf, 10)
    body_text(section3p2, pdf)
    subheader_text(section3ah, pdf)
    body_text(section3a, pdf)
    subheader_text(section3bh, pdf)
    body_text(section3b, pdf)
    subheader_text(section3ch, pdf)
    body_text(section3c, pdf)
    subheader_text(section3dh, pdf)
    body_text(section3d, pdf)
    subheader_text(section3eh, pdf)
    body_text(section3e, pdf)

    # Detailed clauses for section 4
    header_text(section4title, pdf, 14)
    subheader_text(section4ah, pdf, 10)
    body_text(section4a, pdf)
    subheader_text(section4bh, pdf, 10)
    body_text(section4b, pdf)
    subheader_text(section4ch, pdf, 10)
    body_text(section4c, pdf)
    subheader_text(section4dh, pdf, 10)
    body_text(section4d, pdf)
    subheader_text(section4eh, pdf, 10)
    body_text(section4e, pdf)
    if rental_type == "1 BEDROOM" or rental_type == "2 BEDROOM":
        subheader_text(section4fh, pdf, 10)
        body_text(section4f, pdf)
        subheader_text(section4gh, pdf, 10)
        body_text(section4g, pdf)

    # Detailed clauses for section 5
    header_text(section5title, pdf, 14)
    subheader_text(section5ah, pdf, 10)
    body_text(section5a, pdf)
    subheader_text(section5bh, pdf, 10)
    body_text(section5b, pdf)
    subheader_text(section5ch, pdf, 10)
    body_text(section5c, pdf)
    subheader_text(section5dh, pdf, 10)
    body_text(section5d, pdf)
    subheader_text(section5eh, pdf, 10)
    body_text(section5e, pdf)
    subheader_text(section5fh, pdf, 10)
    body_text(section5f, pdf)
    subheader_text(section5gh, pdf, 10)
    body_text(section5g, pdf)
    subheader_text(section5hh, pdf, 10)
    body_text(section5h, pdf)
    subheader_text(section5ih, pdf, 10)
    body_text(section5i, pdf)
    subheader_text(section5jh, pdf, 10)
    body_text(section5j, pdf)
    subheader_text(section5kh, pdf, 10)
    body_text(section5k, pdf)
    subheader_text(section5lh, pdf, 10)
    body_text(section5l, pdf)
    subheader_text(section5mh, pdf, 10)
    body_text(section5m, pdf)
    subheader_text(section5nh, pdf, 10)
    body_text(section5n, pdf)
    subheader_text(section5oh, pdf, 10)
    body_text(section5o, pdf)
    if property_type == 'HDB FLAT':
        subheader_text(section5ph, pdf, 10)
        body_text(section5p, pdf)

    # Signatures and Witness
    pdf.ln(10)
    header_text("IN WITNESS WHEREOF", pdf, 14)
    body_text("the parties hereto have hereunto set their hands the day and year first above written.", pdf, 10)
    body_text_ns("**SIGNED by the LANDLORD**", pdf)
    body_text_ns(f"Name: **{landlord_name}**", pdf)
    body_text_ns(f"NRIC: **{landlord_id}**", pdf)
    body_text_ns("**SIGNED by the TENANT**", pdf)
    body_text_ns(f"Name: **{tenant_name}**", pdf)
    body_text_ns(f"NRIC: **{tenant_id}**", pdf)

    pdf.ln(10)
    header_text("List of occupier(s)", pdf, 12)
    pdf.set_font("Helvetica", size = 10)

    TABLE_DATA = (
        ("Name of Occupier", "ID No."),
        (tenant_name, tenant_id),
    )
    with pdf.table() as table:
        for data_row in TABLE_DATA:
            row = table.row()
            for datum in data_row:
                row.cell(datum)


    pdf.ln(10)
    body_text(f"**The Landlord:** Please inspect the original employment or work pass, original travel and identification documents of the prospective foreign tenants.", pdf)
    body_text(f"**The Tenant:** The Tenant is required to inform the Landlord of any visitors staying in the house from time to time. The Tenant shall be responsible to ensure that the number of Tenants and occupiers shall not exceed the maximum occupants allowed by the authorities.", pdf)

    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Helvetica", style="I", size=10)
    pdf.write(5, "This document has been anonymized to remove all personally identifiable information (PII) for public release. All names, addresses, contact information, identification numbers, and financial details have been replaced with generic placeholders or fictional information.")

    pdf.output(f"tenancy_agreement_{ref_no}.pdf")
    print(f"Tenancy Agreement PDF generated: tenancy_agreement_{ref_no}.pdf")

# Calls the tenancy generator function to create a few sample tenancy agreements
generate_tenancy_agreement("HDB FLAT", "2 ROOM", "HDBflat_whole")
generate_tenancy_agreement("HDB FLAT", "1 BEDROOM", "HDBflat_bedroom")
generate_tenancy_agreement("CONDO / PRIVATE APARTMENT", "3 ROOM", "Condo_whole")
generate_tenancy_agreement("CONDO / PRIVATE APARTMENT", "1 BEDROOM", "Condo_bedroom")
generate_tenancy_agreement("LANDED", "TERRACE HOUSE", "Landed")