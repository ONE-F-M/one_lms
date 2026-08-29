frappe.ui.form.ControlTextEditor = class ControlTextEditor extends frappe.ui.form.ControlCode {
	make_wrapper() {
		super.make_wrapper();
	}

	make_input() {
		this.has_input = true;
		this.make_quill_editor();
	}

	make_quill_editor() {
		const that = this;
		this.quill_container = $("<div>").appendTo(this.input_area);

		tinymce.init({
			target: this.input_area,
			toolbar:
				"undo redo | bold italic underline strikethrough | fontfamily fontsize blocks | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist checklist | forecolor backcolor casechange permanentpen formatpainter removeformat | pagebreak | charmap emoticons | fullscreen  preview save print | insertfile media pageembed template link anchor codesample | a11ycheck ltr rtl | showcomments addcomment | footnotes | mergetags | customHRButton | image rotateleft rotateright",
			font_size_formats: "10px 11px 12px 14px 15px 16px 18px 24px 36px",
			plugins: [
				"autolink",
				"charmap",
				"emoticons",
				"fullscreen",
				"help",
				"image",
				"link",
				"lists",
				"searchreplace",
				"table",
				"visualblocks",
				"visualchars",
				"wordcount",
				"media",
				"anchor",
			],
			powerpaste_googledocs_import: "prompt",
			entity_encoding: "raw",
			convert_urls: true,
			content_css: false,
			toolbar_sticky: false,
			promotion: false,
			default_link_target: "_blank",
			height: 500,
			file_picker_types: "image",
			file_picker_callback: (cb, value, meta) => {
				const input = document.createElement("input");
				input.setAttribute("type", "file");
				input.setAttribute("accept", "image/*");

				input.addEventListener("change", (e) => {
					const file = e.target.files[0];

					const reader = new FileReader();
					reader.addEventListener("load", () => {
						const id = "blobid" + new Date().getTime();
						const blobCache = tinymce.activeEditor.editorUpload.blobCache;
						const base64 = reader.result.split(",")[1];
						const blobInfo = blobCache.create(id, file, base64);
						blobCache.add(blobInfo);

						cb(blobInfo.blobUri(), { title: file.name });
					});
					reader.readAsDataURL(file);
				});

				input.click();
			},
			// content_style: "body { font-family: Calibri, sans-serif; }",
			font_family_formats:
				"Andale Mono=andale mono,times; Arial=arial,helvetica,sans-serif; Arial Black=arial black,avant garde; Book Antiqua=book antiqua,palatino; Calibri=Calibri, sans-serif; Comic Sans MS=comic sans ms,sans-serif; Courier New=courier new,courier; Georgia=georgia,palatino; Helvetica=helvetica; Impact=impact,chicago; Symbol=symbol; Tahoma=tahoma,arial,helvetica,sans-serif; Terminal=terminal,monaco; Times New Roman=times new roman,times; Trebuchet MS=trebuchet ms,geneva; Verdana=verdana,geneva; Webdings=webdings; Wingdings=wingdings,zapf dingbats",
			setup: function (editor) {
				that.editor_id = editor.id;

				editor.ui.registry.addButton("customHRButton", {
					icon: "horizontal-rule",
					tooltip: "Insert Horizontal Rule",
					onAction: function (_) {
						editor.selection.setContent("<hr/>");
					},
				});

				editor.ui.registry.addButton("rotateleft", {
					text: "⟲",
					tooltip: "Rotate Left",
					onAction: function () {
						rotateImage(editor, -90);
					},
				});

				editor.ui.registry.addButton("rotateright", {
					text: "⟳",
					tooltip: "Rotate Right",
					onAction: function () {
						rotateImage(editor, 90);
					},
				});

				editor.on("Change", function (e) {
					that.parse_validate_and_set_in_model(e.level.content);
				});
				editor.on("init", function (e) {
					editor.setContent(that.value || "");

					let tinyMCEContainer = $(".tox-editor-container");
					tinyMCEContainer.css("z-index", 0);
				});
			},
		});
		this.activeEditor = tinymce.activeEditor;
	}

	set_formatted_input(value) {
		if (!this.frm) return;

		if (!value) {
			this.activeEditor.setContent("");
			return;
		}

		let bookmark = this.activeEditor.selection
			? this.activeEditor.selection.getBookmark(2, true)
			: null;
		this.activeEditor.setContent(value);

		if (bookmark) {
			this.activeEditor.selection.moveToBookmark(bookmark);
		}
	}

	get_input_value() {
		return this.activeEditor.getContent();
	}
};

function rotateImage(editor, angle) {
	let img = editor.selection.getNode(); // Get selected image
	if (img.nodeName === "IMG") {
		let currentRotation = img.getAttribute("data-rotation") || 0;
		let newRotation = (parseInt(currentRotation) + angle) % 360;
		img.style.transform = `rotate(${newRotation}deg)`;
		img.setAttribute("data-rotation", newRotation);
	}
}
