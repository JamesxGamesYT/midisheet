import subprocess
import sys
import os
from PIL import Image, UnidentifiedImageError
import numpy as np
import ffmpeg
import py_midicsv as pm
import matplotlib.pyplot as plt


def convert_to_frame(video):
    global fps, x_pixels, y_pixels
    print("ok!!!")
    try:
        os.mkdir("./"+video[:video.find(".")])
    except:
        pass
    try:
        files = os.listdir("./"+video[:video.find(".")])
        if "img00001.png" not in files:
            subprocess.run(["ffmpeg","-i", video, "-an", "-f", "image2", "-vf", "scale=640:-1", "./" + video[:video.find(".")] + "/img%05d.png"])
    except:
        subprocess.run(["ffmpeg","-i", video, "-an", "-f", "image2", "-vf", "scale=640:-1","./" + video[:video.find(".")] + "/img%05d.png"])
    probe = ffmpeg.probe(video)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    # # print(video_info)
    fps = int(video_info['r_frame_rate'].split('/')[0])
    # x_pixels = video_info['width']
    # y_pixels = video_info['height']
    # print(fps, x_pixels, y_pixels)
    # fps = 25
    x_pixels = 640
    y_pixels = 320

def analyze(video, half_note_pixel_length=8, whole_note_pixel_length=12):
    # burn: half - 8, whole - 12
    # nocturne: half - 9, whole - 14
    # half_note_pixel_length = 9
    # whole_note_pixel_length = 14
    files = os.listdir("./"+video[:video.find(".")])
    # analyze_amount = round(array.shape[0] * 1/24)
    all_average_pixels = []
    average_pixels_array = []
    whole_notes = []
    first_note = None
    # Extra notes from each frame
    array = np.asarray(Image.open("./"+video[:video.find(".")]+"/img00001.png"))
    background_colors = array[0] 

    for file in files:
    # for file in files[6500:]:
        if file.startswith("img") and file.endswith(".png"):
            print(file)
            try:
                array = np.asarray(Image.open("./"+video[:video.find(".")]+"/"+file))
            except UnidentifiedImageError:
                print(sorted(list(average_pixels)))
                all_average_pixels.extend(list(average_pixels))
                continue
            # if "00001" in file:
            #     background_colors = array[0] 
            # first.save("test.png")
            # current = []
            # for x, pixel in enumerate(array[0]):
            #     if sum(pixel) > 10:
            #         current.append(1)
            #     else:
            #         current.append(0)
            # status = "neither"
            # for x, pixel in enumerate(array[0]):
            #     if current[x] == 1 and previous[x] == 1:
            #         if status == "neither":
            #             status = "both exist"
            #             begin_pixel = x
            #         elif status == "current exists":
            #             average_pixel = (x + begin_pixel)/2
            #             # print(x-begin_pixel, average_pixel)
            #             if x-begin_pixel > 8:
            #                 average_pixels.add(round(average_pixel))
            #             status = "both exist"
            #             begin_pixel = x
            #     elif current[x] == 1 and previous[x] == 0:
            #         if status == "neither":
            #             status = "both exist"
            #             begin_pixel = x
            #         elif status == "both_exist":
            #             average_pixel = (x + begin_pixel)/2
            #             # print(x-begin_pixel, average_pixel)
            #             if x-begin_pixel > 8:
            #                 average_pixels.add(round(average_pixel))
            #             status = "current exists"
            #             begin_pixel = x
            #     elif current[x] == 0:
            #         if status == "both exist" or status == "current exists":
            #             average_pixel = (x + begin_pixel)/2
            #             # print(x-begin_pixel, average_pixel)
            #             if x-begin_pixel > 8:
            #                 average_pixels.add(round(average_pixel))
                # if current[x] == 1 and previous[x] == 1:
                #     if status == "neither"
                # if current[x] == 1 and previous[x] == 0:


            note_found = False
            average_pixels = set()
            brightness = 0
            pixel_brightnesses = []
            for x, pixel in enumerate(array[0]):
                # distance = sum(pixel)
                distance = sum(pixel)-sum(background_colors[x])
                # distance = pixel[0]-background_colors[x][0]+pixel[1]-background_colors[x][1]+pixel[2]-background_colors[x][2]
                # if file == "img00120.png":
                #     print(distance, sum(pixel), x)
                if note_found == False:
                    if distance > 75:
                        note_found = True
                        begin_pixel = x
                        brightness += sum(pixel)
                        pixel_brightnesses.append([distance, x])
                else:
                    if distance <= 75:
                        note_found = False
                        # print(x-begin_pixel, average_pixel)
                        average_brightness = brightness/(x-begin_pixel)
                        # print(x-begin_pixel, x, begin_pixel)
                        if x-begin_pixel >= half_note_pixel_length and average_brightness > 75:
                            print(x-begin_pixel, average_brightness, "accepted")
                            note_num = max(round((x-begin_pixel)/whole_note_pixel_length), 1)
                            average_pixel = ((x-whole_note_pixel_length*(note_num-1) + begin_pixel)/2)
                            for i in range(note_num):
                                average_pixels.add(round(average_pixel+whole_note_pixel_length*i))
                                # if round(average_pixel+whole_note_pixel_length*i) == 188:
                                    # raise Exception(file, "188 found")
                            if note_num == 1 and x-begin_pixel > whole_note_pixel_length:
                                whole_notes.append(round(average_pixel))
                        else:
                            print(x-begin_pixel, average_brightness, "rejected!")
                        brightness = 0
                    else:
                        brightness += distance
            print(sorted(list(average_pixels)))
            if not first_note:
                if len(average_pixels) > 0:
                    first_note = sorted(list(average_pixels))[0]
            all_average_pixels.extend(list(average_pixels))
            average_pixels_array.append(list(average_pixels))
            # previous = current
    
    sorted_all_average_pixels = sorted(list(set(all_average_pixels)))
    pixel_to_aggregate_mapping = {}
    print(sorted_all_average_pixels)
    sep = True
    aggregate_list = []
    # Map similar values to a single value
    for i in range(len(sorted_all_average_pixels)-1):
        diff = sorted_all_average_pixels[i+1]-sorted_all_average_pixels[i]
        if diff < 4*(whole_note_pixel_length/14):
            sep = False
            if len(aggregate_list) > 0:
                # if sorted_all_average_pixels[i]-aggregate_list[0] < half_note_pixel_length: 
                print(sorted_all_average_pixels[i]-aggregate_list[0], aggregate_list[0], sorted_all_average_pixels[i], (half_note_pixel_length/2.0))
                if (sorted_all_average_pixels[i]-aggregate_list[0]) < (half_note_pixel_length/2.0): 
                    aggregate_list.append(sorted_all_average_pixels[i])
                else:
                    aggregate_list.append(sorted_all_average_pixels[i])
                    average = round(sum(aggregate_list)/len(aggregate_list))
                    for num in aggregate_list:
                        pixel_to_aggregate_mapping[num] = average
                    sep = True
                    aggregate_list = []
            else:
                aggregate_list.append(sorted_all_average_pixels[i])
        else:
            if sep == False:
                aggregate_list.append(sorted_all_average_pixels[i])
                average = round(sum(aggregate_list)/len(aggregate_list))
                for num in aggregate_list:
                    pixel_to_aggregate_mapping[num] = average
                sep = True
            else:
                pixel_to_aggregate_mapping[sorted_all_average_pixels[i]] = sorted_all_average_pixels[i]
            aggregate_list = []
    # Add ending x values to map
    if sep == True:
        pixel_to_aggregate_mapping[sorted_all_average_pixels[-1]] = sorted_all_average_pixels[-1]
    else:
        aggregate_list.append(sorted_all_average_pixels[-1])
        average = round(sum(aggregate_list)/len(aggregate_list))
        for num in aggregate_list:
            pixel_to_aggregate_mapping[num] = average

    print(pixel_to_aggregate_mapping)
    # Substitute old values for modified ones
    modified_all_average_pixels = []
    for i in range(len(average_pixels_array)):
        for j in range(len(average_pixels_array[i])):
            average_pixels_array[i][j] = pixel_to_aggregate_mapping[average_pixels_array[i][j]]
        modified_all_average_pixels.extend(average_pixels_array[i])
    sorted_modified_all_average_pixels = sorted(list(set(modified_all_average_pixels)))
    print(sorted_modified_all_average_pixels, "sorted_modified_all_average_pixels")

    # # Substitute values in the whole notes as well
    # modified_whole_notes = []
    # for whole_note in whole_notes:
    #     modified_whole_notes.append(pixel_to_aggregate_mapping[whole_note])
    # modified_whole_notes = list(sorted(set(modified_whole_notes)))
    # print(list(sorted(set(modified_whole_notes))), "modified_whole_notes")
    # modified_whole_notes_differences = []
    # for i in range(len(modified_whole_notes)-1):
    #     modified_whole_notes_differences.append(modified_whole_notes[i+1]-modified_whole_notes[i])
    # print(modified_whole_notes_differences, "modified_whole_notes_differences") 

    # Modify the first note as well
    modified_first_note = pixel_to_aggregate_mapping[first_note]
    print("first note: ", modified_first_note)
    first_note_midi_value = int(input("The midi representation of the first note is: "))

    # Graph the song's transcribed notes
    plt.figure(figsize=(5,40))
    x_coords = []
    y_coords = []
    for i, frame in enumerate(average_pixels_array):
        for note in frame:
            x_coords.append(i)
            y_coords.append(note)
    plt.scatter(y_coords,x_coords,s=1)
    plt.savefig("song transcription.png")

    # Find half-step differences between note values
    modified_notes_to_midi = {}
    # sorted_differences = []
    # sorted_minimum_halfstep_differences = []
    # for i in range(len(sorted_modified_all_average_pixels)):
    #     division = 7.4*(whole_note_pixel_length/14)
    #     # division = 7.4+difference_to_standard
    #     # print(division)
    #     # print(7.4*whole_note_pixel_length/14)
    #     sorted_differences.append((sorted_modified_all_average_pixels[i]-modified_first_note))
    #     sorted_minimum_halfstep_differences.append(round((sorted_modified_all_average_pixels[i]-modified_first_note)/(division)))
        # sorted_minimum_halfstep_differences.append((sorted_modified_all_average_pixels[i]-minimum_value)/7.2)
    # relative_differences_to_c_to_midi_difference = {
    #     0 : 0,
    #     1 : 1,
    #     2 : 2,
    #     3 : 3,
    #     4 : 4,
    #     5 : 4,
    #     6 : 5,
    #     7 : 6,
    #     8 : 7,
    #     9 : 8,
    #     10 : 9,
    #     11 : 10,
    #     12 : 11,
    #     13 : 11,
    # }
    note_size = 12
    # x_value_diffs_to_c_to_midi_diffs = {
    #     0 : 0,
    #     8 : 1,
    #     12 : 2,
    #     16 : 3,
    #     24 : 4,
    #     36 : 5,
    #     42 : 6,
    #     48 : 7,
    #     54 : 8,
    #     60 : 9,
    #     78 : 10,
    #     72 : 11,
    #     84 : 12,
    # }
    x_value_diffs_to_c_to_midi_diffs = {
        0 : 0,
        8 : 1,
        13 : 2,
        22 : 3,
        26 : 4,
        39 : 5,
        43 : 6,
        52 : 7,
        58 : 8,
        65 : 9,
        73 : 10,
        77 : 11,
        88 : 12,
    }
    # x_value_diffs_to_c_to_midi_diffs = {
    #     0 : 0,
    #     8 : 1,
    #     14 : 2,
    #     18 : 3,
    #     28 : 4,
    #     42 : 5,
    #     46 : 6,
    #     56 : 7,
    #     63 : 8,
    #     70 : 9,
    #     78 : 10,
    #     84 : 11,
    #     98 : 12,
    # }
    # print(sorted_differences, "sorted_differences")
    # print(sorted_minimum_halfstep_differences, "sorted_minimum_half_step_differences")
    # # Set the median equal to middle C (can be transposed)
    # median = sorted_minimum_halfstep_differences[round(len(sorted_minimum_halfstep_differences)/2)]
    # for i in range(len(sorted_minimum_halfstep_differences)):
    #     midi_note = first_note_midi_value + sorted_minimum_halfstep_differences[i] // 14 + relative_differences_to_c_to_midi_difference[sorted_minimum_halfstep_differences[i] % 14]
    #     midi_note = 60+sorted_minimum_halfstep_differences[i]-median
    #     modified_notes_to_midi[sorted_modified_all_average_pixels[i]] = midi_note
    # print(modified_notes_to_midi)

    minimum_differences = []
    for i in range(len(sorted_modified_all_average_pixels)):
        minimum_differences.append((sorted_modified_all_average_pixels[i]-modified_first_note))
    print(minimum_differences, "minimum_differences")
    x_value_diffs_to_midi_diffs = {}
    first_note_distance_from_c = (first_note_midi_value - 60) % 12
    first_note_x_value_diff_from_c = res = dict((v,k) for k,v in x_value_diffs_to_c_to_midi_diffs.items())[first_note_distance_from_c]
    # first_note_x_value_diff_from_c = list(x_value_diffs_to_c_to_midi_diffs.keys())[list(x_value_diffs_to_c_to_midi_diffs.values()).find(first_note_distance_from_c)]
    for x_value, midi_diff in x_value_diffs_to_c_to_midi_diffs.items():
        x_value_diffs_to_midi_diffs[(x_value - first_note_x_value_diff_from_c) % 88] = (midi_diff - first_note_distance_from_c) % 12
    print(x_value_diffs_to_midi_diffs)
    print(sorted(x_value_diffs_to_midi_diffs.keys()))

    for i in range(len(minimum_differences)):
        x_value = minimum_differences[i]
        x_value_diff = x_value % 88
        still_below = True
        for j, key in enumerate(sorted(x_value_diffs_to_midi_diffs.keys())):
            if key >= x_value_diff:
                if j == 0:
                    modified_x_value_diff = key
                else:
                    if abs(key - x_value_diff) >= abs(x_value_diff - sorted(list(x_value_diffs_to_midi_diffs.keys()))[j-1]):
                        print("ok first was used")
                        print(sorted_modified_all_average_pixels[i], key, x_value_diff, sorted(list(x_value_diffs_to_midi_diffs.keys()))[j-1], j)
                        modified_x_value_diff = sorted(list(x_value_diffs_to_midi_diffs.keys()))[j-1]
                    else:
                        print("ok second was used")
                        print(sorted_modified_all_average_pixels[i], key, x_value_diff, sorted(list(x_value_diffs_to_midi_diffs.keys()))[j-1], j)

                        modified_x_value_diff = key
                break
        midi_note = (x_value // 88) * 12 + x_value_diffs_to_midi_diffs[modified_x_value_diff]
        print(sorted_modified_all_average_pixels[i], (x_value // 88) * 12, x_value_diffs_to_midi_diffs[modified_x_value_diff], modified_x_value_diff, x_value_diff)
        modified_notes_to_midi[sorted_modified_all_average_pixels[i]] = midi_note + first_note_midi_value
        
    print(modified_notes_to_midi, "modified_notes_to_midi")



    # Find pressed notes
    # keys are Modified raw note values, values are begining frame
    previous_frame_notes = {}
    # Elements are lists of [note, begin_frame, end_frame]
    note_presses = []
    for i, notes in enumerate(average_pixels_array):
        notes_to_delete = []
        for note in previous_frame_notes:
            if note not in notes:
                note_presses.append([modified_notes_to_midi[note], previous_frame_notes[note], "on"])
                note_presses.append([modified_notes_to_midi[note], i-1, "off"])
                notes_to_delete.append(note)
        for note in notes:
            if note not in previous_frame_notes:
                previous_frame_notes[note] = i
        for note in notes_to_delete:
            del previous_frame_notes[note]
    # Add ending notes, if there are any
    for note, begin in previous_frame_notes.items():
        note_presses.append([modified_notes_to_midi[note], begin, "on"])
        note_presses.append([modified_notes_to_midi[note], i+1, "off"])
    note_presses = sorted(note_presses, key=lambda x: x[1])
    print(note_presses)
    # Volume of each midi note
    velocity = 110
    midi_array = []
    milliseconds_per_tick = 2.6
    milliseconds_per_frame = 1000/fps
    time_multiplier = milliseconds_per_frame/milliseconds_per_tick
    # Each frame is 1/30 seconds = 33.3 milliseconds. Each tick is 2.6 milliseconds.
    # Therefore each frame corresponds to 12.8 ticks.
    # 192 TICKS PER BEAT
    # 48 TICKS PER SIXTEENTH NOTE
    # 24 TICKS PER THIRTY-SECONDETH NOTE
    # TEMPO CHANGE, MAYBE?
    # 120 BEATS PER MINUTE
    midi_array.append("0,0,Header,1,3,192\n")
    midi_array.append("1,0,Start_track\n")
    midi_array.append("1,0,Title_t,"+video[:video.rfind(".")]+"\n")
    # TIME SIGNATURE - MAYBE A WAY TO CHANGE
    midi_array.append("1,0,Key_signature,-1,major\n")
    midi_array.append("1,0,Time_signature,4,2,24,8\n")
    midi_array.append("1,0,Tempo,500000\n")
    midi_array.append("1,0,End_track\n")
    midi_array.append("2,0,Start_track\n")
    # Should be bright acoustic piano??? this 1 needs to be checked
    midi_array.append("2,0,Program_c,0,1\n")
    for note_press in note_presses:
        modified_time = (round(time_multiplier*note_press[1]) // 24)*24
        # print(round(time_multiplier*note_press[1]), modified_time, "IF A TIME WAS CHANGED:")
        if note_press[2] == "on":
            midi_array.append("2," + str(modified_time) + ",Note_on_c,0,"+str(note_press[0])+",110\n")
        else:
            midi_array.append("2," + str(modified_time) + ",Note_off_c,0,"+str(note_press[0])+",110\n")
    midi_array.append("2,0,End_track\n")
    midi_array.append("0,0,End_of_file")
    if video[:video.find(".")]+".csv" in files:
        os.remove(video[:video.find(".")]+".csv")
    with open(video[:video.find(".")]+".csv", "w") as f:
        f.writelines(midi_array)
    midi_object = pm.csv_to_midi(midi_array)
    if video[:video.find(".")]+".mid" in files:
        os.remove(video[:video.find(".")]+".mid")
    with open(video[:video.find(".")]+".mid", "wb") as f:
        midi_writer = pm.FileWriter(f)
        midi_writer.write(midi_object)
    # print("It should be: [0,2,9,12,14,21,26,28,33]")
    # print(diff)
    # print(sum(diff)/2)













if __name__ == "__main__":
    video = sys.argv[1]
    convert_to_frame(video)
    analyze(video)