from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Restaurant, Menu, MenuSection, MenuItem, DietaryRestriction, ProcessingLog
from .forms import MenuUploadForm
from .api_integration import process_menu_pdf  # Import the process_menu_pdf function
from decimal import Decimal
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from os import remove
from decimal import InvalidOperation
from django.utils import timezone
from django.db import transaction

def menu_detail(request, restaurant_id):
    """
    Display the menu details for a specific restaurant.
    """
    restaurant = get_object_or_404(Restaurant, restaurant_id=restaurant_id)
    menus = Menu.objects.filter(restaurant=restaurant)
    return render(request, 'menu_app/menu_detail.html', {'restaurant': restaurant, 'menus': menus})


def upload_menu(request):
    """
    Handle the menu PDF upload and send it for processing with Claude.
    Debugging version to trace menu processing steps.
    """
    if request.method == 'POST':
        form = MenuUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data['menu_pdf']
            
            # Save the uploaded PDF temporarily for processing
            file_name = default_storage.save('uploads/' + pdf_file.name, ContentFile(pdf_file.read()))
            file_path = default_storage.path(file_name)
            
            try:
                with transaction.atomic():
                    # Process the menu PDF using Claude
                    menu_data = process_menu_pdf(file_path)
                    
                    # Debug: Print full menu data
                    print("DEBUG: Full Menu Data Received:")
                    import json
                    print(json.dumps(menu_data, indent=2))
                    
                    # Get or create the restaurant object based on extracted data
                    restaurant_name = menu_data.get("restaurant_name", "Unknown Restaurant")
                    restaurant_location = menu_data.get("restaurant_location", "Unknown Location")
                    
                    restaurant, _ = Restaurant.objects.get_or_create(
                        name=restaurant_name,
                        location=restaurant_location
                    )
                    
                    # Create new menu
                    latest_menu = Menu.objects.filter(restaurant=restaurant).order_by('-version').first()
                    version = (latest_menu.version + 1) if latest_menu else 1
                    
                    menu = Menu.objects.create(
                        restaurant=restaurant,
                        version=version,
                        date=timezone.now().date()
                    )
                    
                    # Debug: Check menu sections
                    menu_sections = menu_data.get('menu_sections', [])
                    print(f"DEBUG: Number of menu sections: {len(menu_sections)}")
                    
                    # Process menu sections
                    for section_index, section_data in enumerate(menu_sections, 1):
                        print(f"DEBUG: Processing section {section_index}: {section_data}")
                        
                        # Validate section data
                        if not section_data.get('section_name'):
                            print(f"WARNING: Section {section_index} missing section name")
                            continue
                        
                        section = MenuSection.objects.create(
                            menu=menu,
                            section_name=section_data['section_name'],
                            section_order=section_index
                        )
                        
                        # Debug: Check items in section
                        section_items = section_data.get('items', [])
                        print(f"DEBUG: Number of items in section {section_index}: {len(section_items)}")
                        
                        # Process items in each section
                        for item_index, item_data in enumerate(section_items, 1):
                            print(f"DEBUG: Processing item {item_index}: {item_data}")
                            
                            # Validate item data
                            if not item_data.get('name'):
                                print(f"WARNING: Item {item_index} in section {section_index} missing name")
                                continue
                            
                            try:
                                price = Decimal(str(item_data.get('price', '0')))
                            except (InvalidOperation, TypeError):
                                print(f"WARNING: Invalid price for item {item_index}")
                                price = Decimal('0.00')
                            
                            # Handle dietary restriction
                            dietary_label = item_data.get('dietary_restriction')
                            dietary_restriction = None
                            if dietary_label:
                                dietary_restriction, _ = DietaryRestriction.objects.get_or_create(
                                    label=dietary_label
                                )
                            
                            # Create menu item with detailed logging
                            try:
                                menu_item = MenuItem.objects.create(
                                    section=section,
                                    name=item_data.get('name', ''),
                                    description=item_data.get('description', ''),
                                    price=price,
                                    dietary_restriction=dietary_restriction
                                )
                                print(f"DEBUG: Successfully created menu item: {menu_item.name}")
                            except Exception as item_error:
                                print(f"ERROR creating menu item: {item_error}")
                    
                    # Create success log entry
                    ProcessingLog.objects.create(
                        menu=menu,
                        status="Success",
                        error_message="",
                        timestamp=timezone.now()
                    )
                    
                    return redirect('menu_app:menu_detail', restaurant_id=restaurant.restaurant_id)
                    
            except Exception as e:
                # Detailed error logging
                import traceback
                print(f"FULL ERROR TRACE: {traceback.format_exc()}")
                
                # Create error log entry without menu reference
                ProcessingLog.objects.create(
                    menu=None,
                    status="Error",
                    error_message=str(e),
                    timestamp=timezone.now()
                )
                return JsonResponse({
                    'status': 'error',
                    'message': f'Error processing menu: {str(e)}'
                })
                
            finally:
                # Clean up the temporary file
                try:
                    remove(file_path)
                except OSError:
                    pass  # Ignore cleanup errors
                    
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid form submission.'
            })
            
    else:
        form = MenuUploadForm()
        
    return render(request, 'menu_app/upload_menu.html', {'form': form})