# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Entity'
        db.create_table('entities_entity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=450)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=25)),
            ('subtype', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('summary', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('web_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('blog_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('twitter_handle', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
            ('aliases', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('founded_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('deadpooled_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('cb_type', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
            ('cb_updated', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('cb_permalink', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
            ('cb_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('li_uniq_id', self.gf('django.db.models.fields.CharField')(max_length=150, null=True)),
            ('li_univ_name', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('li_type', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('li_last_scanned', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('li_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('total_money', self.gf('django.db.models.fields.CharField')(max_length=15, null=True, blank=True)),
            ('no_employees', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('size_range', self.gf('django.db.models.fields.CharField')(max_length=45, null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
        ))
        db.send_create_signal('entities', ['Entity'])

        # Adding M2M table for field domains on 'Entity'
        db.create_table('entities_entity_domains', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entity', models.ForeignKey(orm['entities.entity'], null=False)),
            ('industry', models.ForeignKey(orm['entities.industry'], null=False))
        ))
        db.create_unique('entities_entity_domains', ['entity_id', 'industry_id'])

        # Adding model 'Image'
        db.create_table('entities_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity', self.gf('django.db.models.fields.related.ForeignKey')(related_name='images', to=orm['entities.Entity'])),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=450)),
            ('source', self.gf('django.db.models.fields.CharField')(max_length=450, null=True)),
            ('logo_type', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('license', self.gf('django.db.models.fields.TextField')(null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(default='active', max_length=15)),
        ))
        db.send_create_signal('entities', ['Image'])

        # Adding model 'Financing'
        db.create_table('entities_financing', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('target', self.gf('django.db.models.fields.related.ForeignKey')(related_name='target', to=orm['entities.Entity'])),
            ('round_code', self.gf('django.db.models.fields.CharField')(max_length=15)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=15, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(max_length=5)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('source_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('entities', ['Financing'])

        # Adding model 'Investment'
        db.create_table('entities_investment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('investor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='investor', to=orm['entities.Entity'])),
            ('financing', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['entities.Financing'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=15, decimal_places=2)),
        ))
        db.send_create_signal('entities', ['Investment'])

        # Adding model 'Industry'
        db.create_table('entities_industry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('li_code', self.gf('django.db.models.fields.CharField')(max_length=5, null=True)),
            ('li_group', self.gf('django.db.models.fields.CharField')(max_length=15, null=True)),
        ))
        db.send_create_signal('entities', ['Industry'])

        # Adding model 'Office'
        db.create_table('entities_office', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('entity', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['entities.Entity'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=450, null=True, blank=True)),
            ('is_hq', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('addr_1', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('addr_2', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('addr_3', self.gf('django.db.models.fields.CharField')(max_length=150, null=True, blank=True)),
            ('postal_code', self.gf('django.db.models.fields.CharField')(max_length=45, null=True, blank=True)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=250, null=True, blank=True)),
            ('state_code', self.gf('django.db.models.fields.CharField')(max_length=45, null=True, blank=True)),
            ('country_code', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('latitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=7)),
            ('longitude', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=10, decimal_places=7)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('entities', ['Office'])


    def backwards(self, orm):
        # Deleting model 'Entity'
        db.delete_table('entities_entity')

        # Removing M2M table for field domains on 'Entity'
        db.delete_table('entities_entity_domains')

        # Deleting model 'Image'
        db.delete_table('entities_image')

        # Deleting model 'Financing'
        db.delete_table('entities_financing')

        # Deleting model 'Investment'
        db.delete_table('entities_investment')

        # Deleting model 'Industry'
        db.delete_table('entities_industry')

        # Deleting model 'Office'
        db.delete_table('entities_office')


    models = {
        'entities.entity': {
            'Meta': {'object_name': 'Entity'},
            'aliases': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'blog_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'cb_permalink': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'cb_type': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'cb_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'cb_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'deadpooled_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'domains': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['entities.Industry']", 'symmetrical': 'False'}),
            'founded_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'li_last_scanned': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'li_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'li_uniq_id': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True'}),
            'li_univ_name': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'li_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '450'}),
            'no_employees': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'size_range': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'subtype': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'total_money': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'twitter_handle': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'web_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'entities.financing': {
            'Meta': {'object_name': 'Financing'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '15', 'decimal_places': '2'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'investors': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['entities.Entity']", 'through': "orm['entities.Investment']", 'symmetrical': 'False'}),
            'round_code': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'source_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'target'", 'to': "orm['entities.Entity']"}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'entities.image': {
            'Meta': {'object_name': 'Image'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'entity': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'images'", 'to': "orm['entities.Entity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'license': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '450'}),
            'logo_type': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'source': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'active'", 'max_length': '15'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'entities.industry': {
            'Meta': {'object_name': 'Industry'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'li_code': ('django.db.models.fields.CharField', [], {'max_length': '5', 'null': 'True'}),
            'li_group': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        'entities.investment': {
            'Meta': {'object_name': 'Investment'},
            'amount': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '15', 'decimal_places': '2'}),
            'financing': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['entities.Financing']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'investor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'investor'", 'to': "orm['entities.Entity']"})
        },
        'entities.office': {
            'Meta': {'object_name': 'Office'},
            'addr_1': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'addr_2': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'addr_3': ('django.db.models.fields.CharField', [], {'max_length': '150', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '250', 'null': 'True', 'blank': 'True'}),
            'country_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '450', 'null': 'True', 'blank': 'True'}),
            'entity': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['entities.Entity']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_hq': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '7'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '10', 'decimal_places': '7'}),
            'postal_code': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True', 'blank': 'True'}),
            'state_code': ('django.db.models.fields.CharField', [], {'max_length': '45', 'null': 'True', 'blank': 'True'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['entities']