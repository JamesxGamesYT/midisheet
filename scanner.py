import subprocess
import sys
import os
from PIL import Image, UnidentifiedImageError
import numpy as np
import ffmpeg
import json
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
    print(video_info)
    fps = int(video_info['r_frame_rate'].split('/')[0])/int(video_info['r_frame_rate'].split('/')[1])
    print(fps)
    # x_pixels = video_info['width']
    # y_pixels = video_info['height']
    # print(fps, x_pixels, y_pixels)
    # fps = 25
    x_pixels = 640
    y_pixels = 320

def analyze(video, analyzed=False):
    # burn: half - 8, whole - 12
    # sigma: half - 8, whole - 12
    # nocturne: half - 9, whole - 14
    half_note_pixel_length = 7
    whole_note_pixel_length = 12
    files = os.listdir("./"+video[:video.find(".")])
    if not analyzed:
        # analyze_amount = round(array.shape[0] * 1/24)
        all_average_pixels = []
        average_pixels_array = []
        whole_notes = []
        first_note = None
        # Extra notes from each frame
        # WHAT THE BACKGROUND IS SHOULD BE CHANGEABLE
        array = np.asarray(Image.open("./"+video[:video.find(".")]+"/img00002.png"))
        background_colors = array[0] 

        for file in files:
        # for file in files[:440]:
            if file.startswith("img") and file.endswith(".png"):
                print(file)
                try:
                    array = np.asarray(Image.open("./"+video[:video.find(".")]+"/"+file))
                except UnidentifiedImageError:
                    print(sorted(list(average_pixels)))
                    all_average_pixels.extend(list(average_pixels))
                    continue
                note_found = False
                average_pixels = set()
                total_distances = 0
                pixel_total_distances = []
                # WHAT ROW OF PIXELS IT IS SHOULD BE CHANGEABLE
                for x, pixel in enumerate(array[0]):
                    # distance = sum(pixel)
                    distance = abs(sum(pixel)-sum(background_colors[x]))
                    # distance = pixel[0]-background_colors[x][0]+pixel[1]-background_colors[x][1]+pixel[2]-background_colors[x][2]
                    if note_found == False:
                        if distance > 75:
                            note_found = True
                            begin_pixel = x
                            total_distances += distance
                            pixel_total_distances.append([distance, x])
                    else:
                        # if distance <= 75 or x-begin_pixel >= whole_note_pixel_length:
                        #     note_found = False
                        #     average_brightness = total_distances/(x-begin_pixel)
                        #     if average_brightness > 75:
                        #         # print(total_distances, pixel_total_distances)
                        #         average_pixel = sum(ele[0]*ele[1] for ele in pixel_total_distances)/(total_distances)
                        #         average_pixels.add(round(average_pixel))
                        #         begin_pixel = x
                        #     pixel_total_distances = []
                        #     total_distances = 0
                        if distance <= 75:
                            note_found = False
                            # print(x-begin_pixel, average_pixel)
                            average_brightness = total_distances/(x-begin_pixel)
                            # print(x-begin_pixel, x, begin_pixel)
                            if x-begin_pixel >= half_note_pixel_length and average_brightness > 75:
                                # print(x-begin_pixel, average_brightness, "accepted")
                                note_num = max(round((x-begin_pixel)/whole_note_pixel_length), 1)
                                average_pixel = ((x-whole_note_pixel_length*(note_num-1) + begin_pixel)/2)
                                for i in range(note_num):
                                    average_pixels.add(round(average_pixel+whole_note_pixel_length*i))
                                    if (round(average_pixel+whole_note_pixel_length*i) == 362):
                                        print("YO THIS IS ONE OF THEM")
                                if note_num == 1 and x-begin_pixel > whole_note_pixel_length:
                                    whole_notes.append(round(average_pixel))
                            # else:
                                # print(x-begin_pixel, average_brightness, "rejected!")
                            total_distances = 0
                        else:
                            pixel_total_distances.append([distance, x])
                            total_distances += distance
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
            current = sorted_all_average_pixels[i]
            diff = sorted_all_average_pixels[i+1]-current
            if diff < 4*(whole_note_pixel_length/14):
                # sep holds whether the space before current is a seperation between aggregate values
                sep = False
                if len(aggregate_list) > 0:
                    # if current-aggregate_list[0] < half_note_pixel_length: 
                    print(current-aggregate_list[0], aggregate_list[0], current, (half_note_pixel_length/2.0))
                    if (current-aggregate_list[0]) < (half_note_pixel_length/2.0): 
                        aggregate_list.append(current)
                    else:
                        average = round(sum(aggregate_list)/len(aggregate_list))
                        for num in aggregate_list:
                            pixel_to_aggregate_mapping[num] = average
                        sep = True
                        aggregate_list = []
                        # aggregate_list.append(current)
                        pixel_to_aggregate_mapping[current] = current
                else:
                    aggregate_list.append(current)
            else:
                if sep == False:
                    aggregate_list.append(current)
                    average = round(sum(aggregate_list)/len(aggregate_list))
                    for num in aggregate_list:
                        pixel_to_aggregate_mapping[num] = average
                    sep = True
                else:
                    pixel_to_aggregate_mapping[current] = current
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

        # Modify the first note as well
        modified_first_note = pixel_to_aggregate_mapping[first_note]
        print("first note: ", modified_first_note)
        recieved = input("The midi representation of the first note is: ")
        if "\x1b[A" in recieved:
            recieved = recieved[6:]
        first_note_midi_value = int(recieved)

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


        with open(video[:video.find(".")]+".txt", "w") as f:
            f.write(str(modified_first_note) + "\n" + str(first_note_midi_value))
        with open(video[:video.find(".")]+"_array.txt", "a") as f:
            for time in average_pixels_array:
                f.write(str(time)+"\n")
        with open(video[:video.find(".")]+".json", "w") as f:
            json.dump(sorted_modified_all_average_pixels,f)
    else:
        with open(video[:video.find(".")]+".txt", "r") as f:
            modified_first_note, first_note_midi_value = [int(x) for x in f.read().split("\n")]
        with open(video[:video.find(".")]+"_array.txt", "r") as f:
            # average_pixels_array = []
            average_pixels_array = []
            for line in f.read().split("\n"):
                try:
                    average_pixels_array.append(eval(line))
                except:
                    pass
        with open(video[:video.find(".")]+".json", "r") as f:
            sorted_modified_all_average_pixels = json.load(f)
    # Find half-step differences between note values
    modified_notes_to_midi = {}
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
        # 86 : 12,
        87 : 12,
        # 88 : 12,
    }

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
        x_value_diffs_to_midi_diffs[(x_value - first_note_x_value_diff_from_c) % 86] = (midi_diff - first_note_distance_from_c) % 12
    x_value_diffs_to_midi_diffs[86] = 12
    print(x_value_diffs_to_midi_diffs)
    print(sorted(x_value_diffs_to_midi_diffs.keys()))

    for i in range(len(minimum_differences)):
        x_value = minimum_differences[i]
        x_value_diff = x_value % 86
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
        midi_note = (x_value // 86) * 12 + x_value_diffs_to_midi_diffs[modified_x_value_diff]
        print(sorted_modified_all_average_pixels[i], (x_value // 86) * 12, x_value_diffs_to_midi_diffs[modified_x_value_diff], modified_x_value_diff, x_value_diff)
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
        # modified_time = (round(time_multiplier*note_press[1]) // 192)*192   
        modified_time = (round(time_multiplier*note_press[1]) // 48)*48   
        # modified_time = (round(time_multiplier*note_press[1]) // 24)*24   
        # modified_time = (round(time_multiplier*note_press[1]))
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
    if len(sys.argv) > 2:
        analyzed = sys.argv[2]
        analyze(video, analyzed=analyzed)
    else:
        analyze(video)