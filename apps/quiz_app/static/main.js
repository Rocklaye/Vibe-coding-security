document.addEventListener('DOMContentLoaded', function() {
    const container = document.getElementById('questions-container');
    const addBtn = document.getElementById('add-question-btn');
    
    if (container && addBtn) {
        let questionCount = 0;

        function addQuestionBlock() {
            questionCount++;
            const block = document.createElement('div');
            block.className = 'question-block p-4 mb-4 border rounded';
            block.innerHTML = `
                <div class="d-flex justify-content-between">
                    <h5>Question ${questionCount}</h5>
                    ${questionCount > 1 ? '<button type="button" class="btn btn-sm btn-danger remove-btn">Supprimer</button>' : ''}
                </div>
                <div class="mb-3">
                    <input type="text" class="form-control" name="question[]" required placeholder="Posez votre question ici...">
                </div>
                <div class="row">
                    <div class="col-md-6 mb-2">
                        <div class="input-group">
                            <span class="input-group-text">A</span>
                            <input type="text" class="form-control" name="optA[]" required placeholder="Option A">
                        </div>
                    </div>
                    <div class="col-md-6 mb-2">
                        <div class="input-group">
                            <span class="input-group-text">B</span>
                            <input type="text" class="form-control" name="optB[]" required placeholder="Option B">
                        </div>
                    </div>
                    <div class="col-md-6 mb-2">
                        <div class="input-group">
                            <span class="input-group-text">C</span>
                            <input type="text" class="form-control" name="optC[]" required placeholder="Option C">
                        </div>
                    </div>
                    <div class="col-md-6 mb-2">
                        <div class="input-group">
                            <span class="input-group-text">D</span>
                            <input type="text" class="form-control" name="optD[]" required placeholder="Option D">
                        </div>
                    </div>
                </div>
                <div class="mt-3 w-50">
                    <label class="form-label text-success fw-bold">Bonne réponse :</label>
                    <select class="form-select border-success" name="correct[]" required>
                        <option value="A">Option A</option>
                        <option value="B">Option B</option>
                        <option value="C">Option C</option>
                        <option value="D">Option D</option>
                    </select>
                </div>
            `;
            container.appendChild(block);

            // Add event listener for delete button
            if (questionCount > 1) {
                block.querySelector('.remove-btn').addEventListener('click', function() {
                    block.remove();
                    updateQuestionNumbers();
                });
            }
        }

        function updateQuestionNumbers() {
            const blocks = container.querySelectorAll('.question-block');
            blocks.forEach((block, index) => {
                block.querySelector('h5').innerText = `Question ${index + 1}`;
            });
            questionCount = blocks.length;
        }

        // Initialize with one question
        addQuestionBlock();

        // Add more on click
        addBtn.addEventListener('click', addQuestionBlock);
    }
});