document.addEventListener('DOMContentLoaded', function() {
    const imageSelect = document.getElementById('imageSelect');
    const displayImage = document.getElementById('displayImage');

    // Function to fetch the list of image files from the JSON file
    async function fetchImageList() {
        try {
            const response = await fetch('processed_files/image_list.json'); // Path to your JSON file
            const images = await response.json();
            populateSelectBox(images);
        } catch (error) {
            console.error('Error fetching image list:', error);
        }
    }

    // Function to populate the select box with image options
    function populateSelectBox(images) {
        images.forEach(image => {
            const option = document.createElement('option');
            option.value = image.fileName;
            option.textContent = image.displayName;
            imageSelect.appendChild(option);
        });
    }

    // Event listener to handle image selection
    imageSelect.addEventListener('change', function() {
        const selectedImage = imageSelect.value;
        if (selectedImage) {
            displayImage.src = `processed_files/images/${selectedImage}`; // Adjust the path to your images directory if needed
        } else {
            displayImage.src = '';
        }
    });

    // Fetch the image list on page load
    fetchImageList();
});