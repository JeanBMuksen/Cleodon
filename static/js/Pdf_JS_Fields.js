var price = this.getField('price').value; 
var quantity = this.getField('quantity').value;
var total=parseFloat((parseFloat(price)*parseFloat(quantity) || 0).toFixed(2));
this.getField('total').value=total;