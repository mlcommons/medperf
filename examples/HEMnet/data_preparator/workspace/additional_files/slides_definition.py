def slides_definition(pipeline_state):
    """
    This preserves the behavior of the original code of assuming the user only
    sends paired slides into the input directory.
    If unpaired slides are sent, this code does NOT check for that!
    """
    from pathlib import Path

    input_data_dir = Path(pipeline_state.host_input_data_path)
    slides = []

    for slide in input_data_dir.glob("*.svs"):
        name = slide.name
        slides.append(name)
    slides.sort()
    TP53_slides = [slide for slide in slides if "TP53" in slide]
    HE_slides = [slide for slide in slides if "HandE" in slide]
    Paired_slides = list(zip(TP53_slides, HE_slides))
    prefixes = [paired_slide[0][:-10] for paired_slide in Paired_slides]
    return prefixes
