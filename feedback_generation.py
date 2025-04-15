import pandas as pd
import random

# Expanded sample data for each type of feedback
positive_feedback = [
    "Professor Jack is amazing! His lectures are very clear and engaging.",
    "I really enjoyed this class. Jack explains the concepts very well.",
    "Great teaching style and always available to help!",
    "One of the best professors I've had so far.",
    "The lectures were well structured and informative.",
    "Jack brings real-world examples that make the material come alive.",
    "I appreciate the extra resources Jack provides outside of class.",
    "His enthusiasm is contagious and motivates me to learn.",
    "Jack is patient and answers all our questions thoroughly.",
    "Fantastic course organization and clear objectives every week.",
    "The feedback on assignments is constructive and helpful.",
    "Jack’s office hours are very helpful and well-timed.",
    "I feel more confident in the subject thanks to Jack's teaching.",
    "The interactive quizzes are a great way to reinforce learning.",
    "Jack uses technology effectively to enhance lectures.",
    "Very approachable and supportive professor.",
    "Jack encourages critical thinking and discussion.",
    "This class exceeded my expectations in every way.",
    "I would recommend this course to all my peers.",
    "Jack's passion for the subject is evident in every lecture.",
    # Additional positive feedback samples
    "I love how Jack incorporates current research into his lessons.",
    "Jack's group activities are both fun and educational.",
    "I always leave class feeling inspired and motivated.",
    "Jack's use of case studies really helps solidify my understanding.",
    "The pacing of this course is perfect for learning effectively."
]

negative_feedback = [
    "I didn’t understand most of what he was saying.",
    "His teaching method is boring and unhelpful.",
    "Too fast-paced and doesn’t explain enough.",
    "I didn't find the classes useful.",
    "Very poor communication and not approachable.",
    "Lectures feel disorganized and jump between topics.",
    "Assignments are unclear and grading seems arbitrary.",
    "Jack rarely addresses student questions in class.",
    "The course content feels outdated and irrelevant.",
    "I often leave class more confused than when I arrived.",
    "Lacks engagement and the lectures are monotone.",
    "Office hours are hard to schedule and unhelpful.",
    "Slides are text-heavy and not visually appealing.",
    "Feedback on exams is minimal and not constructive.",
    "I struggle to stay focused during his lectures.",
    "The pace is uneven, sometimes too slow then too fast.",
    "His examples are not related to the course material.",
    "I feel lost because he doesn't recap previous topics.",
    "The course seems rushed towards the end.",
    "I wouldn’t take another class with this professor.",
    # Additional negative feedback samples
    "I feel the lectures are too repetitive and redundant.",
    "Jack doesn't provide enough practice problems.",
    "I find the reading materials confusing and unhelpful.",
    "His voice is monotone and puts me to sleep.",
    "The assignments have nothing to do with lecture content."
]

neutral_feedback = [
    "The class was okay, nothing special.",
    "Jack was average as a professor.",
    "I attended most of the lectures, they were fine.",
    "Neither good nor bad, just a normal experience.",
    "Content was decent, delivery could be better.",
    "Sometimes the lectures are interesting, sometimes not.",
    "I met my learning objectives, but it wasn’t exciting.",
    "Jack covers the syllabus but doesn’t go beyond.",
    "The workload was manageable but not challenging.",
    "Group discussions were okay but could be improved.",
    "The textbook is helpful, but the lectures repeat it.",
    "I had no strong feelings either way about this course.",
    "Attendance was easy, but participation was optional.",
    "Exams reflect the lectures but aren’t too hard.",
    "The class environment is neutral and predictable.",
    "I might take another course if required, not by choice.",
    "Jack is polite but doesn’t inspire much enthusiasm.",
    "The pace is steady but not engaging.",
    "I got the necessary credit but not much more.",
    "Standard lecture format, nothing innovative.",
    # Additional neutral feedback samples
    "The course met my expectations exactly.",
    "I neither loved nor hated this class.",
    "The lectures were fine but lacked excitement.",
    "Jack does his job adequately.",
    "I have a neutral stance on this professor."
]

offensive_feedback = [
    "Jack is a f***ing joke. Worst prof ever.",
    "This class is s**t. Can't believe I paid for this.",
    "Total b*llshit, waste of time.",
    "He's just an a**. Doesn’t care at all.",
    "What the hell was that course even about?",
    "I want my money back, this is garbage.",
    "His lectures are dogsh*t and pointless.",
    "Such a f**king waste, I'm dropping this course.",
    "Jack acts like he knows everything but he sucks.",
    "This professor is a moron, pure a**holery.",
    "Worst academic experience, total f*ck-up.",
    "He’s a lazy a** who reads slides verbatim.",
    "What an incompetent buffoon teaching here.",
    "I’m sick of his pathetic attempts at teaching.",
    "Absolute f**kery in every lecture.",
    "He’s clueless and his lectures are trash.",
    "This course is a dumpster fire."
]

personal_info_feedback = [
    "My student ID is 123456 and I think Jack needs to change his style.",
    "Classroom B-402 has a broken projector, Jack should report it.",
    "As a student from section A2, I feel this class lacked depth.",
    "My email is student2025@univ.edu, and I need help from Jack.",
    "My roll number 21ECE45 faced issues with his lecture notes.",
    "I live in Dorm 5, room 210, and can’t attend morning classes.",
    "My phone number is 555-1234, please call me about my grade.",
    "I’m from the honors program, so I expected more rigor.",
    "My SSN is 987-65-4321, please verify my enrollment.",
    "I use wheelchair access and need the lectures recorded.",
    "I’m on financial aid and need accommodations for assignments.",
    "My campus ID card is expired, can Jack help renew it?",
    "My address is 123 University Ave, Apt 4, Cityville.",
    "I’m in the debate club and need extra credit.",
    "My advisor is Dr. Smith, he recommended this course.",
    "My birthday is 01/01/2003, can I get an extension?"
]

# Combine and randomly choose 100 responses
all_feedback = (
    positive_feedback * 8 +  # more weight for positives
    negative_feedback * 8 +
    neutral_feedback * 6 +
    offensive_feedback * 3 +
    personal_info_feedback * 3
)

random.shuffle(all_feedback)
sample_feedback = random.sample(all_feedback, 100)

# Create DataFrame
df = pd.DataFrame(sample_feedback, columns=["feedback"])

# Save to CSV
file_path = "faculty_feedback.csv"
df.to_csv(file_path, index=False)

print(f"Saved 100 feedback samples to {file_path}")
