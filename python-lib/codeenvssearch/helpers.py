# Create function to extract the base package name
def get_base_package(package):
    base_package = package

    # Handle packages that are referenced with an URL or path
    pattern = r"^(\/|http|git\+http|\-\-find)"
    if re.match(pattern, package):
        base_package = base_package.split('/')[-1]
        if '-' in base_package:
            base_package = base_package.split('-')[0].replace('_', '-')

    # Extract the base package
    # Extract the base package
    pattern = r"^([\w\-\.\[\]]+)"
    base_package = (
        base_package
        .strip()
        .replace('"', '')
        .replace("'", '')
        .replace('#', '')
        .replace('_', '-')
    )

    try:
        base_package = re.match(pattern, base_package).group(1)
    except:
        print(f'Exception when packaged={base_package}')
        base_package = None

    return base_package

