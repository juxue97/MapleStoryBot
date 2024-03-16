import os

def rename_files(folder_path):
    if not os.path.exists(folder_path):
        print(f"Folder '{folder_path}' does not exist.")
        return

    # Loop through each file and rename
    for i,image in enumerate(os.listdir(folder_path)):
        old_path = os.path.join(folder_path, image)
        
        # Modify the renaming logic as needed
        new_name = '{}.txt'.format(i)  # Example: Replace 'old_string' with 'new_string'

        new_path = os.path.join(folder_path, new_name)

        # Perform the rename
        os.rename(old_path, new_path)

if __name__ == "__main__":
    folder_path = 'images/backup_labels'  # Change to your folder path
    rename_files(folder_path)