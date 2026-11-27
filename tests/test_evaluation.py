from agent.evaluation import match_contact, match_deadline, match_eligibility, match_location


def test_eligibility_compares_verdict_word_only():
    assert match_eligibility("Yes, open to all undergraduates", "Yes")
    assert not match_eligibility("Unclear - visa not mentioned", "No")


def test_location():
    assert match_location("In-Person (Hangzhou)", "in-person")
    assert not match_location("Remote", "Hybrid")


def test_deadline_formats():
    assert match_deadline("March 1, 2027", "2027-03-01")
    assert match_deadline("Rolling admissions", "Rolling")
    assert not match_deadline("2027-03-02", "2027-03-01")


def test_contact_names():
    assert match_contact("Dr. Haoyang Li", "Haoyang Li")
    assert match_contact("Not Found", "Unknown")
    assert not match_contact("Prof. Zhang Wei", "Haoyang Li")
