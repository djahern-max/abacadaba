# 4.01: "Courses in subjects that undergo frequent changes ... must be
# reviewed ... at least once a year to verify the currency of the content.
# Other courses must be reviewed ... at least every two years." Feature 021
# stores this choice as Course.review_cycle ('annual'/'biennial'); this
# feature is the first to actually compare it against a clock.
REVIEW_WINDOW_DAYS = {"annual": 365, "biennial": 730}

# A review that only surfaces the day it lapses has already lapsed - see
# current-feature.md, Part 3. Applied to both the review-currency and
# expiration sections of the dashboard.
DUE_SOON_WINDOW_DAYS = 60

# 9.02.2 item 3: "Course documentation must include an expiration date ...
# For individual courses, the expiration date is no longer than one year
# from the date of purchase or enrollment." abacadaba has no per-enrollment
# purchase date - every participant enrolls whenever they like - so the one
# year window is measured from the course's own review date instead, the
# closest thing this application has to "when this content was current as
# of." See app/models/course.py's Course.expires_on and
# CourseDetailsForm.jsx's client-side default.
EXPIRATION_WINDOW_DAYS = 365
