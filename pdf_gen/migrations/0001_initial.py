# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Price'
        db.create_table('pdf_gen_price', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(1980, 2, 2, 0, 0))),
        ))
        db.send_create_signal('pdf_gen', ['Price'])

        # Adding model 'PriceTemplate'
        db.create_table('pdf_gen_pricetemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('price', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['pdf_gen.Price'])),
            ('site', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('language', self.gf('django.db.models.fields.CharField')(default='default', max_length=15)),
            ('template_file', self.gf('elfinder.fields.ElfinderField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal('pdf_gen', ['PriceTemplate'])


    def backwards(self, orm):
        # Deleting model 'Price'
        db.delete_table('pdf_gen_price')

        # Deleting model 'PriceTemplate'
        db.delete_table('pdf_gen_pricetemplate')


    models = {
        'pdf_gen.price': {
            'Meta': {'object_name': 'Price'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(1980, 2, 2, 0, 0)'}),
            'name': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'pdf_gen.pricetemplate': {
            'Meta': {'object_name': 'PriceTemplate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'default'", 'max_length': '15'}),
            'price': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['pdf_gen.Price']"}),
            'site': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'template_file': ('elfinder.fields.ElfinderField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['pdf_gen']