from agent.extraction import NOT_FOUND, build_analysis_prompt, parse_fields


def test_plain_format():
    text = "SPONSORSHIP: International friendly\nDEADLINE: 2027-03-01\nCONTACT: Dr. Li"
    f = parse_fields(text)
    assert f["SPONSORSHIP"] == "International friendly"
    assert f["DEADLINE"] == "2027-03-01"
    assert f["CONTACT"] == "Dr. Li"
    assert f["LOCATION"] == NOT_FOUND


def test_markdown_bold_and_bullets():
    # Gemini often answers like this; the old parser returned "Not Found" for all of it.
    text = "**SPONSORSHIP:** Unknown\n- **Deadline:** Rolling\n* Location: Remote\n**ELIGIBILITY**: Yes, open to all undergrads"
    f = parse_fields(text)
    assert f["SPONSORSHIP"] == "Unknown"
    assert f["DEADLINE"] == "Rolling"
    assert f["LOCATION"] == "Remote"
    assert f["ELIGIBILITY"] == "Yes, open to all undergrads"


def test_values_containing_colons_and_dashes_survive():
    f = parse_fields("DEADLINE: March 1, 2027 - 23:59 AoE")
    assert f["DEADLINE"] == "March 1, 2027 - 23:59 AoE"


def test_first_occurrence_wins_and_empty_input():
    f = parse_fields("CONTACT: Prof. A\nCONTACT: Prof. B")
    assert f["CONTACT"] == "Prof. A"
    assert all(v == NOT_FOUND for v in parse_fields("").values())
    assert all(v == NOT_FOUND for v in parse_fields(None).values())


def test_custom_fields():
    f = parse_fields("NAME: Cursor\nCATEGORY: Coding & Agents", ["NAME", "CATEGORY", "DESCRIPTION"])
    assert f == {"NAME": "Cursor", "CATEGORY": "Coding & Agents", "DESCRIPTION": NOT_FOUND}


def test_prompt_uses_profile_override():
    prompt = build_analysis_prompt("Title", "Body", "Freshman", {"nationality": "Kenyan"})
    assert "Kenyan" in prompt and "Freshman" in prompt
    assert "Chinese X1 student visa" in prompt  # defaults still fill missing keys
