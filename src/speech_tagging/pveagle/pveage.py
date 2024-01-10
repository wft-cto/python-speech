import pveagle


access_key = "Ygc7uEluQbKlt+OPC2G5XrNh+NhSWzToKepBChF4S5THx9w26vw3EQ=="
eagle_profiler = pveagle.create_profiler(access_key)

def get_next_enroll_audio_data(num_samples):
    pass


percentage = 0.0
while percentage < 100.0:
    percentage, feedback = eagle_profiler.enroll(get_next_enroll_audio_data(eagle_profiler.min_enroll_samples))
    print(feedback.name)